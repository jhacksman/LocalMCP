import * as fs from 'fs/promises';
import * as path from 'path';
import * as crypto from 'crypto';
import { createWorker } from 'tesseract.js';
import * as pdfParse from 'pdf-parse';
import * as sharp from 'sharp';

// Configure environment variables
const TEMP_DIR = process.env.TEMP_DIR || './temp';
const OCR_WORKER_THREADS = parseInt(process.env.OCR_WORKER_THREADS || '2', 10);
const PDF_WORKER_THREADS = parseInt(process.env.PDF_WORKER_THREADS || '2', 10);

// Ensure temp directory exists
async function ensureTempDir() {
  try {
    await fs.mkdir(TEMP_DIR, { recursive: true });
  } catch (error) {
    console.error('Error creating temp directory:', error);
  }
}

// Initialize temp directory
ensureTempDir();

interface PdfExtractionResult {
  text: string;
  page_count: number;
  extracted_pages: number[];
}

interface OcrResult {
  text: string;
  confidence: number;
  processing_time: number;
}

interface DocumentConversionResult {
  text: string;
  original_format: string;
  processing_time: number;
}

export class DocumentService {
  private ocrWorkers: any[] = [];
  private ocrWorkerInitialized = false;

  constructor() {
    // Initialize OCR workers
    this.initializeOcrWorkers();
  }

  private async initializeOcrWorkers() {
    if (this.ocrWorkerInitialized) return;
    
    try {
      // Create a single worker for now to minimize VRAM usage
      const worker = await createWorker('eng');
      this.ocrWorkers.push(worker);
      this.ocrWorkerInitialized = true;
      console.log('OCR worker initialized');
    } catch (error) {
      console.error('Error initializing OCR workers:', error);
      throw new Error(`Failed to initialize OCR workers: ${error}`);
    }
  }

  public async extractPdfText(
    filePath: string,
    pageNumbers?: number[]
  ): Promise<PdfExtractionResult> {
    try {
      // Ensure file exists
      await fs.access(filePath);
      
      // Read PDF file
      const dataBuffer = await fs.readFile(filePath);
      
      // Parse PDF
      const startTime = Date.now();
      const pdf = await pdfParse(dataBuffer);
      
      // Extract text from specific pages if requested
      let extractedText = pdf.text;
      let extractedPages = Array.from({ length: pdf.numpages }, (_, i) => i + 1);
      
      if (pageNumbers && pageNumbers.length > 0) {
        // Filter to only requested pages
        // Note: This is a simplified implementation
        // A more complete implementation would extract text page by page
        extractedPages = pageNumbers;
        // For now, we'll just return the full text since pdf-parse doesn't easily support page-by-page extraction
      }
      
      return {
        text: extractedText,
        page_count: pdf.numpages,
        extracted_pages: extractedPages
      };
    } catch (error: any) {
      console.error('Error extracting PDF text:', error);
      throw new Error(`Failed to extract PDF text: ${error.message}`);
    }
  }

  public async preprocessImage(imagePath: string): Promise<string> {
    try {
      // Ensure temp directory exists
      await ensureTempDir();
      
      // Generate a unique filename for the processed image
      const fileExt = path.extname(imagePath);
      const fileName = path.basename(imagePath, fileExt);
      const processedPath = path.join(TEMP_DIR, `${fileName}-processed${fileExt}`);
      
      // Process the image to improve OCR results
      await sharp(imagePath)
        // Convert to grayscale
        .grayscale()
        // Increase contrast
        .normalize()
        // Remove noise
        .median(1)
        // Resize if too large
        .resize(2000, 2000, {
          fit: 'inside',
          withoutEnlargement: true
        })
        // Save the processed image
        .toFile(processedPath);
      
      return processedPath;
    } catch (error: any) {
      console.error('Error preprocessing image:', error);
      throw new Error(`Failed to preprocess image: ${error.message}`);
    }
  }

  public async performOcr(
    imagePath: string,
    language: string = 'eng',
    preprocess: boolean = true
  ): Promise<OcrResult> {
    try {
      // Ensure OCR workers are initialized
      if (!this.ocrWorkerInitialized) {
        await this.initializeOcrWorkers();
      }
      
      // Preprocess the image if requested
      const processedImagePath = preprocess ? await this.preprocessImage(imagePath) : imagePath;
      
      // Perform OCR
      const startTime = Date.now();
      
      // Use the first worker (we only create one to minimize VRAM usage)
      const worker = this.ocrWorkers[0];
      
      // Set language
      await worker.loadLanguage(language);
      await worker.initialize(language);
      
      // Recognize text
      const { data } = await worker.recognize(processedImagePath);
      
      const processingTime = Date.now() - startTime;
      
      // Clean up temporary file if it was created
      if (preprocess && processedImagePath !== imagePath) {
        try {
          await fs.unlink(processedImagePath);
        } catch (error) {
          console.warn('Error removing temporary file:', error);
        }
      }
      
      return {
        text: data.text,
        confidence: data.confidence / 100, // Convert to 0-1 scale
        processing_time: processingTime
      };
    } catch (error: any) {
      console.error('Error performing OCR:', error);
      throw new Error(`Failed to perform OCR: ${error.message}`);
    }
  }

  public async convertDocumentToText(
    filePath: string,
    outputFormat: string = 'text'
  ): Promise<DocumentConversionResult> {
    try {
      // Ensure file exists
      await fs.access(filePath);
      
      const startTime = Date.now();
      const fileExt = path.extname(filePath).toLowerCase();
      let text = '';
      
      // Process based on file extension
      if (fileExt === '.pdf') {
        // Extract text from PDF
        const pdfResult = await this.extractPdfText(filePath);
        text = pdfResult.text;
      } else if (['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'].includes(fileExt)) {
        // Perform OCR on image
        const ocrResult = await this.performOcr(filePath, 'eng', true);
        text = ocrResult.text;
      } else {
        throw new Error(`Unsupported file format: ${fileExt}`);
      }
      
      const processingTime = Date.now() - startTime;
      
      return {
        text,
        original_format: fileExt.substring(1), // Remove the dot
        processing_time: processingTime
      };
    } catch (error: any) {
      console.error('Error converting document to text:', error);
      throw new Error(`Failed to convert document to text: ${error.message}`);
    }
  }

  public async cleanup() {
    // Terminate OCR workers
    for (const worker of this.ocrWorkers) {
      try {
        await worker.terminate();
      } catch (error) {
        console.warn('Error terminating OCR worker:', error);
      }
    }
    
    this.ocrWorkers = [];
    this.ocrWorkerInitialized = false;
    
    // Clean up temp directory
    try {
      const files = await fs.readdir(TEMP_DIR);
      for (const file of files) {
        await fs.unlink(path.join(TEMP_DIR, file));
      }
    } catch (error) {
      console.warn('Error cleaning up temp directory:', error);
    }
  }
}
