import { ChromaClient, Collection } from 'chromadb';
import type { Metadata } from 'chromadb';
import * as path from 'path';
import * as fs from 'fs';
import * as crypto from 'crypto';

// Configure environment variables
const VECTOR_DB_PATH = process.env.VECTOR_DB_PATH || './data';
const DEFAULT_EMBEDDING_MODEL = process.env.EMBEDDING_MODEL || 'all-MiniLM-L6-v2';

// Ensure data directory exists
if (!fs.existsSync(VECTOR_DB_PATH)) {
  fs.mkdirSync(VECTOR_DB_PATH, { recursive: true });
}

interface EmbeddingResult {
  model: string;
  vector_size: number;
  embedding_id: string;
  embedding: number[];
}

interface SearchResult {
  documents: Array<{
    text: string;
    score: number;
    metadata: Record<string, any>;
  }>;
  total: number;
  search_time: number;
}

export class VectorDBService {
  private chromaClient: ChromaClient;
  private embeddingModel: any;
  private collections: Map<string, Collection> = new Map();
  private modelName: string;
  private modelLoaded: boolean = false;

  constructor() {
    // Initialize ChromaDB client
    this.chromaClient = new ChromaClient({
      path: path.resolve(VECTOR_DB_PATH)
    });
    
    this.modelName = DEFAULT_EMBEDDING_MODEL;
    
    // Load the embedding model
    this.loadEmbeddingModel();
  }

  private async loadEmbeddingModel(): Promise<void> {
    try {
      // Load the feature extraction pipeline
      const { pipeline } = await import('@xenova/transformers');
      this.embeddingModel = await pipeline('feature-extraction', this.modelName);
      this.modelLoaded = true;
      console.log(`Loaded embedding model: ${this.modelName}`);
    } catch (error) {
      console.error('Error loading embedding model:', error);
      throw new Error(`Failed to load embedding model: ${error}`);
    }
  }

  private async getCollection(collectionName: string): Promise<Collection> {
    if (this.collections.has(collectionName)) {
      return this.collections.get(collectionName)!;
    }

    try {
      // Try to get existing collection
      const collection = await this.chromaClient.getCollection({
        name: collectionName
      } as any);
      this.collections.set(collectionName, collection);
      return collection;
    } catch (error) {
      // Create new collection if it doesn't exist
      const collection = await this.chromaClient.createCollection({
        name: collectionName,
        metadata: { 
          'hnsw:space': 'cosine',
          'model': this.modelName
        }
      });
      this.collections.set(collectionName, collection);
      return collection;
    }
  }

  public async generateEmbedding(text: string, model?: string): Promise<EmbeddingResult> {
    // Ensure model is loaded
    if (!this.modelLoaded) {
      await this.loadEmbeddingModel();
    }

    // If a different model is requested, check if we need to reload
    if (model && model !== this.modelName) {
      this.modelName = model;
      this.modelLoaded = false;
      await this.loadEmbeddingModel();
    }

    try {
      // Generate embedding
      const result = await this.embeddingModel(text, {
        pooling: 'mean',
        normalize: true
      });

      // Get the embedding vector
      const embedding = Array.from(result.data) as number[];
      
      // Generate a unique ID for this embedding
      const embeddingId = crypto.createHash('md5').update(text).digest('hex');
      
      return {
        model: this.modelName,
        vector_size: embedding.length,
        embedding_id: embeddingId,
        embedding: embedding
      };
    } catch (error) {
      console.error('Error generating embedding:', error);
      throw new Error(`Failed to generate embedding: ${error}`);
    }
  }

  public async storeDocument(
    text: string, 
    collection: string, 
    metadata: Record<string, any> = {}
  ): Promise<{ document_id: string; collection: string }> {
    // Generate embedding for the text
    const embeddingResult = await this.generateEmbedding(text);
    
    // Get or create collection
    const collectionObj = await this.getCollection(collection);
    
    // Generate a document ID
    const documentId = crypto.createHash('md5').update(`${text}-${Date.now()}`).digest('hex');
    
    // Add the document to the collection
    await collectionObj.add({
      ids: [documentId],
      embeddings: [embeddingResult.embedding],
      metadatas: [{ ...metadata, text }],
      documents: [text]
    });
    
    return {
      document_id: documentId,
      collection
    };
  }

  public async searchVectors(
    query: string,
    collection: string,
    limit: number = 5,
    threshold: number = 0.7
  ): Promise<SearchResult> {
    // Generate embedding for the query
    const startTime = Date.now();
    const queryEmbedding = await this.generateEmbedding(query);
    
    // Get the collection
    const collectionObj = await this.getCollection(collection);
    
    // Search for similar vectors
    const results = await collectionObj.query({
      queryEmbeddings: [queryEmbedding.embedding],
      nResults: limit
    });
    
    // Process results
    const documents: Array<{
      text: string;
      score: number;
      metadata: Record<string, any>;
    }> = [];
    
    if (results.ids && results.ids.length > 0 && results.ids[0].length > 0) {
      for (let i = 0; i < results.ids[0].length; i++) {
        const score = results.distances ? 1 - (results.distances[0][i] || 0) : 0;
        
        // Only include results above the threshold
        if (score >= threshold) {
          const metadata = results.metadatas && results.metadatas[0] ? 
            results.metadatas[0][i] || {} : {};
          
          const text = results.documents && results.documents[0] ? 
            results.documents[0][i] || '' : '';
          
          documents.push({
            text: text as string,
            score,
            metadata: metadata as Record<string, any>
          });
        }
      }
    }
    
    const searchTime = Date.now() - startTime;
    
    return {
      documents,
      total: documents.length,
      search_time: searchTime
    };
  }

  public async getModelInfo(): Promise<{ name: string; vector_size: number }> {
    // Ensure model is loaded
    if (!this.modelLoaded) {
      await this.loadEmbeddingModel();
    }
    
    // Generate a simple embedding to get vector size
    const sampleEmbedding = await this.generateEmbedding('Sample text for vector size check');
    
    return {
      name: this.modelName,
      vector_size: sampleEmbedding.vector_size
    };
  }

  public async listCollections(): Promise<string[]> {
    const collections = await this.chromaClient.listCollections();
    return collections.map((collection: any) => collection.name);
  }
}
