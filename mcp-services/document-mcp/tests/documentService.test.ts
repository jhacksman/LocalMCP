import { expect } from 'chai';
import { describe, it, beforeEach, afterEach } from 'mocha';
import sinon from 'sinon';
import { DocumentService } from '../src/services/documentService';
import * as fs from 'fs/promises';
import * as path from 'path';

describe('Document Service Tests', () => {
  let documentService: DocumentService;
  let fsStub: sinon.SinonStub;
  
  beforeEach(() => {
    // Create a fresh instance for each test
    documentService = new DocumentService();
    
    // Stub fs.readFile to prevent actual file operations
    fsStub = sinon.stub(fs, 'readFile');
    fsStub.resolves(Buffer.from('Test file content'));
  });
  
  afterEach(() => {
    // Restore stubs after each test
    sinon.restore();
  });
  
  describe('PDF Text Extraction', () => {
    it('should extract text from PDF files', async () => {
      // Mock PDF content
      const pdfBuffer = Buffer.from('Mock PDF content');
      fsStub.resolves(pdfBuffer);
      
      // Mock the PDF parsing function
      const pdfParseMock = sinon.stub(documentService as any, 'parsePDF');
      pdfParseMock.resolves({
        text: 'Extracted text from PDF',
        numpages: 5,
        info: { Title: 'Test Document' }
      });
      
      const result = await documentService.extractPDFText('/path/to/document.pdf', [1, 2, 3]);
      
      expect(result).to.have.property('text');
      expect(result.text).to.equal('Extracted text from PDF');
      expect(result.metadata).to.have.property('page_count');
      expect(result.metadata.page_count).to.equal(5);
      expect(result.metadata).to.have.property('extracted_pages');
      expect(result.metadata.extracted_pages).to.deep.equal([1, 2, 3]);
    });
    
    it('should handle PDF extraction errors', async () => {
      // Mock PDF content
      const pdfBuffer = Buffer.from('Mock PDF content');
      fsStub.resolves(pdfBuffer);
      
      // Mock the PDF parsing function to throw an error
      const pdfParseMock = sinon.stub(documentService as any, 'parsePDF');
      pdfParseMock.rejects(new Error('PDF parsing error'));
      
      try {
        await documentService.extractPDFText('/path/to/document.pdf', [1, 2, 3]);
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('PDF parsing error');
      }
    });
    
    it('should handle non-existent PDF files', async () => {
      // Mock fs.readFile to throw a file not found error
      fsStub.rejects(new Error('ENOENT: no such file or directory'));
      
      try {
        await documentService.extractPDFText('/path/to/nonexistent.pdf', [1]);
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('not found');
      }
    });
  });
  
  describe('OCR Image Processing', () => {
    it('should perform OCR on images', async () => {
      // Mock image content
      const imageBuffer = Buffer.from('Mock image content');
      fsStub.resolves(imageBuffer);
      
      // Mock the Tesseract OCR function
      const ocrMock = sinon.stub(documentService as any, 'performOCR');
      ocrMock.resolves({
        text: 'Extracted text from image',
        confidence: 95
      });
      
      const result = await documentService.ocrImage('/path/to/image.jpg', 'eng', true);
      
      expect(result).to.have.property('text');
      expect(result.text).to.equal('Extracted text from image');
      expect(result.metadata).to.have.property('confidence');
      expect(result.metadata.confidence).to.equal(95);
    });
    
    it('should handle OCR errors', async () => {
      // Mock image content
      const imageBuffer = Buffer.from('Mock image content');
      fsStub.resolves(imageBuffer);
      
      // Mock the Tesseract OCR function to throw an error
      const ocrMock = sinon.stub(documentService as any, 'performOCR');
      ocrMock.rejects(new Error('OCR processing error'));
      
      try {
        await documentService.ocrImage('/path/to/image.jpg', 'eng', true);
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('OCR processing error');
      }
    });
    
    it('should preprocess images when requested', async () => {
      // Mock image content
      const imageBuffer = Buffer.from('Mock image content');
      fsStub.resolves(imageBuffer);
      
      // Mock the image preprocessing function
      const preprocessMock = sinon.stub(documentService as any, 'preprocessImage');
      preprocessMock.resolves(Buffer.from('Preprocessed image'));
      
      // Mock the Tesseract OCR function
      const ocrMock = sinon.stub(documentService as any, 'performOCR');
      ocrMock.resolves({
        text: 'Extracted text from preprocessed image',
        confidence: 98
      });
      
      const result = await documentService.ocrImage('/path/to/image.jpg', 'eng', true);
      
      expect(preprocessMock.calledOnce).to.be.true;
      expect(result.text).to.equal('Extracted text from preprocessed image');
      expect(result.metadata.confidence).to.equal(98);
    });
  });
  
  describe('Document Conversion', () => {
    it('should convert documents to text', async () => {
      // Mock document content
      const docBuffer = Buffer.from('Mock document content');
      fsStub.resolves(docBuffer);
      
      // Mock the document conversion function
      const convertMock = sinon.stub(documentService as any, 'convertDocumentToText');
      convertMock.resolves('Converted document text');
      
      const result = await documentService.convertDocument('/path/to/document.docx', 'text');
      
      expect(result).to.have.property('text');
      expect(result.text).to.equal('Converted document text');
      expect(result.metadata).to.have.property('original_format');
      expect(result.metadata.original_format).to.equal('docx');
    });
    
    it('should handle conversion errors', async () => {
      // Mock document content
      const docBuffer = Buffer.from('Mock document content');
      fsStub.resolves(docBuffer);
      
      // Mock the document conversion function to throw an error
      const convertMock = sinon.stub(documentService as any, 'convertDocumentToText');
      convertMock.rejects(new Error('Conversion error'));
      
      try {
        await documentService.convertDocument('/path/to/document.docx', 'text');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('Conversion error');
      }
    });
    
    it('should detect document format from file extension', async () => {
      // Mock document content
      const docBuffer = Buffer.from('Mock document content');
      fsStub.resolves(docBuffer);
      
      // Mock the document conversion function
      const convertMock = sinon.stub(documentService as any, 'convertDocumentToText');
      convertMock.resolves('Converted document text');
      
      await documentService.convertDocument('/path/to/document.docx', 'text');
      
      expect(convertMock.calledWith(docBuffer, 'docx')).to.be.true;
    });
  });
  
  describe('VRAM Management', () => {
    it('should report correct VRAM usage', () => {
      const vramUsage = documentService.getVRAMUsage();
      
      expect(vramUsage).to.have.property('vram_usage_gb');
      expect(vramUsage.vram_usage_gb).to.be.a('number');
      expect(vramUsage.vram_usage_gb).to.be.greaterThan(0);
    });
    
    it('should unload model when requested', async () => {
      const result = await documentService.unloadModel();
      
      expect(result.success).to.be.true;
      expect(result.model_unloaded).to.be.true;
      
      // Check that the model is marked as unloaded
      expect(documentService.isModelLoaded()).to.be.false;
    });
    
    it('should reload model after unloading', async () => {
      // First unload the model
      await documentService.unloadModel();
      
      // Mock the OCR function which should trigger model reload
      const ocrMock = sinon.stub(documentService as any, 'performOCR');
      ocrMock.resolves({
        text: 'Test text',
        confidence: 90
      });
      
      // Mock image content
      const imageBuffer = Buffer.from('Mock image content');
      fsStub.resolves(imageBuffer);
      
      // Perform OCR which should reload the model
      await documentService.ocrImage('/path/to/image.jpg', 'eng', false);
      
      expect(documentService.isModelLoaded()).to.be.true;
    });
  });
  
  describe('Performance Benchmarks', () => {
    it('should extract PDF text within acceptable time', async () => {
      // Mock PDF content
      const pdfBuffer = Buffer.from('Mock PDF content');
      fsStub.resolves(pdfBuffer);
      
      // Mock the PDF parsing function with a fast response
      const pdfParseMock = sinon.stub(documentService as any, 'parsePDF');
      pdfParseMock.resolves({
        text: 'Extracted text from PDF',
        numpages: 5,
        info: { Title: 'Test Document' }
      });
      
      const startTime = Date.now();
      await documentService.extractPDFText('/path/to/document.pdf', [1]);
      const endTime = Date.now();
      
      const executionTime = endTime - startTime;
      expect(executionTime).to.be.lessThan(1000); // Less than 1 second
    });
    
    it('should perform OCR within acceptable time', async () => {
      // Mock image content
      const imageBuffer = Buffer.from('Mock image content');
      fsStub.resolves(imageBuffer);
      
      // Mock the Tesseract OCR function with a fast response
      const ocrMock = sinon.stub(documentService as any, 'performOCR');
      ocrMock.resolves({
        text: 'Extracted text from image',
        confidence: 95
      });
      
      const startTime = Date.now();
      await documentService.ocrImage('/path/to/image.jpg', 'eng', false);
      const endTime = Date.now();
      
      const executionTime = endTime - startTime;
      expect(executionTime).to.be.lessThan(1000); // Less than 1 second
    });
  });
  
  describe('File Handling', () => {
    it('should handle temporary file creation and cleanup', async () => {
      // Mock fs.mkdir to prevent actual directory creation
      const mkdirStub = sinon.stub(fs, 'mkdir');
      mkdirStub.resolves();
      
      // Mock fs.writeFile to prevent actual file writing
      const writeFileStub = sinon.stub(fs, 'writeFile');
      writeFileStub.resolves();
      
      // Mock fs.unlink to prevent actual file deletion
      const unlinkStub = sinon.stub(fs, 'unlink');
      unlinkStub.resolves();
      
      // Mock the createTempFile method
      const tempFilePath = '/tmp/test-file-12345.txt';
      const createTempFileStub = sinon.stub(documentService as any, 'createTempFile');
      createTempFileStub.resolves(tempFilePath);
      
      // Mock the cleanupTempFile method
      const cleanupTempFileStub = sinon.stub(documentService as any, 'cleanupTempFile');
      cleanupTempFileStub.resolves();
      
      // Mock the document conversion function
      const convertMock = sinon.stub(documentService as any, 'convertDocumentToText');
      convertMock.resolves('Converted document text');
      
      await documentService.convertDocument('/path/to/document.docx', 'text');
      
      // Check that temp file methods were called
      expect(createTempFileStub.calledOnce).to.be.true;
      expect(cleanupTempFileStub.calledOnce).to.be.true;
    });
  });
});
