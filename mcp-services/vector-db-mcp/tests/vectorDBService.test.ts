import { expect } from 'chai';
import { describe, it, beforeEach, afterEach } from 'mocha';
import sinon from 'sinon';
import { VectorDBService } from '../src/services/vectorDBService';

describe('Vector DB Service Tests', () => {
  let vectorDBService: VectorDBService;
  
  beforeEach(() => {
    // Create a fresh instance for each test
    vectorDBService = new VectorDBService();
  });
  
  afterEach(() => {
    // Restore stubs after each test
    sinon.restore();
  });
  
  describe('Embedding Generation', () => {
    it('should generate embeddings with correct dimensions', async () => {
      const text = 'This is a test text for embedding generation';
      const result = await vectorDBService.generateEmbedding(text);
      
      expect(result).to.have.property('embedding');
      expect(result.embedding).to.be.an('array');
      expect(result.embedding.length).to.be.greaterThan(0);
      expect(result.model).to.equal('all-MiniLM-L6-v2');
    });
    
    it('should generate consistent embeddings for the same text', async () => {
      const text = 'This is a test text for embedding generation';
      const result1 = await vectorDBService.generateEmbedding(text);
      const result2 = await vectorDBService.generateEmbedding(text);
      
      expect(result1.embedding).to.deep.equal(result2.embedding);
    });
    
    it('should handle empty text input', async () => {
      try {
        await vectorDBService.generateEmbedding('');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('empty text');
      }
    });
  });
  
  describe('Collection Management', () => {
    it('should create a new collection', async () => {
      const collectionName = 'test_collection_' + Date.now();
      const result = await vectorDBService.createCollection(collectionName);
      
      expect(result.success).to.be.true;
      expect(result.collection_name).to.equal(collectionName);
    });
    
    it('should list collections', async () => {
      const collectionName = 'test_collection_' + Date.now();
      await vectorDBService.createCollection(collectionName);
      
      const collections = await vectorDBService.listCollections();
      
      expect(collections).to.be.an('array');
      expect(collections).to.include(collectionName);
    });
    
    it('should delete a collection', async () => {
      const collectionName = 'test_collection_' + Date.now();
      await vectorDBService.createCollection(collectionName);
      
      const result = await vectorDBService.deleteCollection(collectionName);
      
      expect(result.success).to.be.true;
      
      const collections = await vectorDBService.listCollections();
      expect(collections).to.not.include(collectionName);
    });
  });
  
  describe('Document Indexing', () => {
    const testCollection = 'test_index_collection';
    
    beforeEach(async () => {
      // Create a test collection for each test
      try {
        await vectorDBService.createCollection(testCollection);
      } catch (error) {
        // Collection might already exist, ignore error
      }
    });
    
    afterEach(async () => {
      // Clean up test collection after each test
      try {
        await vectorDBService.deleteCollection(testCollection);
      } catch (error) {
        // Collection might not exist, ignore error
      }
    });
    
    it('should index a document', async () => {
      const document = 'This is a test document for indexing';
      const metadata = { title: 'Test Document', author: 'Test Author' };
      const documentId = 'test-doc-' + Date.now();
      
      const result = await vectorDBService.indexDocument(document, metadata, testCollection, documentId);
      
      expect(result.success).to.be.true;
      expect(result.document_id).to.equal(documentId);
      expect(result.collection).to.equal(testCollection);
    });
    
    it('should retrieve a document by ID', async () => {
      const document = 'This is a test document for retrieval';
      const metadata = { title: 'Test Document', author: 'Test Author' };
      const documentId = 'test-doc-' + Date.now();
      
      await vectorDBService.indexDocument(document, metadata, testCollection, documentId);
      
      const result = await vectorDBService.getDocument(testCollection, documentId);
      
      expect(result).to.have.property('document');
      expect(result).to.have.property('metadata');
      expect(result.document).to.equal(document);
      expect(result.metadata).to.deep.equal(metadata);
    });
    
    it('should delete a document', async () => {
      const document = 'This is a test document for deletion';
      const metadata = { title: 'Test Document', author: 'Test Author' };
      const documentId = 'test-doc-' + Date.now();
      
      await vectorDBService.indexDocument(document, metadata, testCollection, documentId);
      
      const result = await vectorDBService.deleteDocument(testCollection, documentId);
      
      expect(result.success).to.be.true;
      
      try {
        await vectorDBService.getDocument(testCollection, documentId);
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('not found');
      }
    });
  });
  
  describe('Similarity Search', () => {
    const testCollection = 'test_search_collection';
    const documents = [
      { text: 'The quick brown fox jumps over the lazy dog', id: 'doc1', metadata: { title: 'Fox Story' } },
      { text: 'A fast brown fox leaps over a sleepy canine', id: 'doc2', metadata: { title: 'Fox Tale' } },
      { text: 'The weather is nice today', id: 'doc3', metadata: { title: 'Weather Report' } },
      { text: 'Climate change affects global temperatures', id: 'doc4', metadata: { title: 'Climate Article' } }
    ];
    
    beforeEach(async () => {
      // Create a test collection and index documents for each test
      try {
        await vectorDBService.createCollection(testCollection);
        
        for (const doc of documents) {
          await vectorDBService.indexDocument(doc.text, doc.metadata, testCollection, doc.id);
        }
      } catch (error) {
        // Collection might already exist, ignore error
      }
    });
    
    afterEach(async () => {
      // Clean up test collection after each test
      try {
        await vectorDBService.deleteCollection(testCollection);
      } catch (error) {
        // Collection might not exist, ignore error
      }
    });
    
    it('should find similar documents', async () => {
      const query = 'brown fox jumping';
      const results = await vectorDBService.similaritySearch(query, testCollection, 2);
      
      expect(results).to.be.an('array');
      expect(results.length).to.equal(2);
      expect(results[0]).to.have.property('id');
      expect(results[0]).to.have.property('score');
      expect(results[0]).to.have.property('document');
      expect(results[0]).to.have.property('metadata');
      
      // The first two documents should be returned as they contain fox and brown
      const resultIds = results.map(r => r.id);
      expect(resultIds).to.include('doc1');
      expect(resultIds).to.include('doc2');
    });
    
    it('should find weather-related documents', async () => {
      const query = 'weather climate temperature';
      const results = await vectorDBService.similaritySearch(query, testCollection, 2);
      
      expect(results).to.be.an('array');
      expect(results.length).to.equal(2);
      
      // The weather-related documents should be returned
      const resultIds = results.map(r => r.id);
      expect(resultIds).to.include('doc3');
      expect(resultIds).to.include('doc4');
    });
    
    it('should respect the top_k parameter', async () => {
      const query = 'document';
      const results = await vectorDBService.similaritySearch(query, testCollection, 1);
      
      expect(results).to.be.an('array');
      expect(results.length).to.equal(1);
    });
  });
  
  describe('VRAM Management', () => {
    it('should report correct VRAM usage', () => {
      const vramUsage = vectorDBService.getVRAMUsage();
      
      expect(vramUsage).to.have.property('vram_usage_gb');
      expect(vramUsage.vram_usage_gb).to.be.a('number');
      expect(vramUsage.vram_usage_gb).to.be.greaterThan(0);
    });
    
    it('should unload model when requested', async () => {
      const result = await vectorDBService.unloadModel();
      
      expect(result.success).to.be.true;
      expect(result.model_unloaded).to.be.true;
      
      // Check that the model is marked as unloaded
      expect(vectorDBService.isModelLoaded()).to.be.false;
    });
    
    it('should reload model after unloading', async () => {
      // First unload the model
      await vectorDBService.unloadModel();
      
      // Then generate an embedding, which should reload the model
      const text = 'This should reload the model';
      const result = await vectorDBService.generateEmbedding(text);
      
      expect(result).to.have.property('embedding');
      expect(vectorDBService.isModelLoaded()).to.be.true;
    });
  });
  
  describe('Performance Benchmarks', () => {
    it('should generate embeddings within acceptable time', async () => {
      const text = 'This is a test text for embedding generation performance benchmark';
      
      const startTime = Date.now();
      await vectorDBService.generateEmbedding(text);
      const endTime = Date.now();
      
      const executionTime = endTime - startTime;
      expect(executionTime).to.be.lessThan(1000); // Less than 1 second
    });
    
    it('should perform similarity search within acceptable time', async () => {
      const testCollection = 'test_perf_collection';
      
      // Create collection and index a few documents
      await vectorDBService.createCollection(testCollection);
      
      for (let i = 0; i < 10; i++) {
        await vectorDBService.indexDocument(
          `This is test document ${i} for performance testing`,
          { index: i },
          testCollection,
          `perf-doc-${i}`
        );
      }
      
      const query = 'test document performance';
      
      const startTime = Date.now();
      await vectorDBService.similaritySearch(query, testCollection, 5);
      const endTime = Date.now();
      
      const executionTime = endTime - startTime;
      expect(executionTime).to.be.lessThan(1000); // Less than 1 second
      
      // Clean up
      await vectorDBService.deleteCollection(testCollection);
    });
  });
});
