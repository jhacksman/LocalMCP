import { expect } from 'chai';
import { describe, it, beforeEach, afterEach } from 'mocha';
import sinon from 'sinon';
import { VRAMManager } from '../src/services/vramManager';
import axios from 'axios';

describe('VRAM Manager Tests', () => {
  let vramManager: VRAMManager;
  let axiosStub: sinon.SinonStub;
  
  beforeEach(() => {
    // Create a fresh instance for each test
    vramManager = new VRAMManager();
    
    // Stub axios to prevent actual HTTP requests
    axiosStub = sinon.stub(axios, 'post');
    axiosStub.resolves({ data: { success: true } });
  });
  
  afterEach(() => {
    // Restore stubs after each test
    sinon.restore();
  });
  
  describe('VRAM Status', () => {
    it('should report correct VRAM status', async () => {
      const status = await vramManager.getVRAMStatus();
      
      expect(status).to.have.property('total_vram_gb');
      expect(status).to.have.property('used_vram_gb');
      expect(status).to.have.property('available_vram_gb');
      expect(status.total_vram_gb).to.be.a('number');
      expect(status.used_vram_gb).to.be.a('number');
      expect(status.available_vram_gb).to.be.a('number');
      expect(status.total_vram_gb).to.equal(64); // Default total VRAM
    });
    
    it('should calculate available VRAM correctly', async () => {
      // Register a service with VRAM usage
      await vramManager.registerService({
        service_name: 'test-service',
        service_url: 'http://localhost:8888',
        vram_usage_gb: 10
      });
      
      const status = await vramManager.getVRAMStatus();
      
      expect(status.used_vram_gb).to.equal(10);
      expect(status.available_vram_gb).to.equal(54); // 64 - 10
    });
  });
  
  describe('Service Registration', () => {
    it('should register a service correctly', async () => {
      const result = await vramManager.registerService({
        service_name: 'test-service',
        service_url: 'http://localhost:8888',
        vram_usage_gb: 5
      });
      
      expect(result.success).to.be.true;
      expect(vramManager.getRegisteredServices()).to.have.lengthOf(1);
      expect(vramManager.getRegisteredServices()[0].service_name).to.equal('test-service');
      expect(vramManager.getRegisteredServices()[0].vram_usage_gb).to.equal(5);
    });
    
    it('should update existing service on re-registration', async () => {
      // Register service first time
      await vramManager.registerService({
        service_name: 'test-service',
        service_url: 'http://localhost:8888',
        vram_usage_gb: 5
      });
      
      // Register same service with different VRAM usage
      const result = await vramManager.registerService({
        service_name: 'test-service',
        service_url: 'http://localhost:8888',
        vram_usage_gb: 10
      });
      
      expect(result.success).to.be.true;
      expect(vramManager.getRegisteredServices()).to.have.lengthOf(1);
      expect(vramManager.getRegisteredServices()[0].vram_usage_gb).to.equal(10);
    });
  });
  
  describe('VRAM Allocation', () => {
    it('should allocate VRAM when available', async () => {
      const result = await vramManager.requestVRAM({
        service_name: 'test-service',
        vram_needed_gb: 20,
        priority: 'medium'
      });
      
      expect(result.success).to.be.true;
      expect(result.vram_allocated_gb).to.equal(20);
      expect(result.unloaded_services).to.be.an('array').that.is.empty;
    });
    
    it('should unload services to free VRAM when needed', async () => {
      // Register services that use most of the VRAM
      await vramManager.registerService({
        service_name: 'service-1',
        service_url: 'http://localhost:8001',
        vram_usage_gb: 20,
        last_used: Date.now() - 3600000 // Used 1 hour ago
      });
      
      await vramManager.registerService({
        service_name: 'service-2',
        service_url: 'http://localhost:8002',
        vram_usage_gb: 30,
        last_used: Date.now() - 7200000 // Used 2 hours ago
      });
      
      // Request more VRAM than available
      const result = await vramManager.requestVRAM({
        service_name: 'test-service',
        vram_needed_gb: 25,
        priority: 'high'
      });
      
      expect(result.success).to.be.true;
      expect(result.vram_allocated_gb).to.equal(25);
      expect(result.unloaded_services).to.be.an('array').that.includes('service-2');
    });
    
    it('should prioritize unloading services based on last used time', async () => {
      // Register services with different last used times
      await vramManager.registerService({
        service_name: 'recent-service',
        service_url: 'http://localhost:8001',
        vram_usage_gb: 20,
        last_used: Date.now() - 60000 // Used 1 minute ago
      });
      
      await vramManager.registerService({
        service_name: 'old-service',
        service_url: 'http://localhost:8002',
        vram_usage_gb: 20,
        last_used: Date.now() - 3600000 // Used 1 hour ago
      });
      
      // Request more VRAM than available
      const result = await vramManager.requestVRAM({
        service_name: 'test-service',
        vram_needed_gb: 30,
        priority: 'high'
      });
      
      expect(result.success).to.be.true;
      expect(result.unloaded_services).to.be.an('array').that.includes('old-service');
      expect(result.unloaded_services).to.not.include('recent-service');
    });
    
    it('should respect service priority when unloading', async () => {
      // Register services with different priorities
      await vramManager.registerService({
        service_name: 'high-priority',
        service_url: 'http://localhost:8001',
        vram_usage_gb: 20,
        priority: 'high',
        last_used: Date.now() - 3600000 // Used 1 hour ago
      });
      
      await vramManager.registerService({
        service_name: 'low-priority',
        service_url: 'http://localhost:8002',
        vram_usage_gb: 20,
        priority: 'low',
        last_used: Date.now() - 3600000 // Used 1 hour ago
      });
      
      // Request more VRAM than available
      const result = await vramManager.requestVRAM({
        service_name: 'test-service',
        vram_needed_gb: 30,
        priority: 'medium'
      });
      
      expect(result.success).to.be.true;
      expect(result.unloaded_services).to.be.an('array').that.includes('low-priority');
      expect(result.unloaded_services).to.not.include('high-priority');
    });
  });
  
  describe('Service Unloading', () => {
    it('should unload a service correctly', async () => {
      // Register a service
      await vramManager.registerService({
        service_name: 'test-service',
        service_url: 'http://localhost:8888',
        vram_usage_gb: 10
      });
      
      // Unload the service
      const result = await vramManager.unloadService('test-service');
      
      expect(result.success).to.be.true;
      expect(result.freed_vram_gb).to.equal(10);
      
      // Check that the service is still registered but marked as unloaded
      const services = vramManager.getRegisteredServices();
      expect(services).to.have.lengthOf(1);
      expect(services[0].service_name).to.equal('test-service');
      expect(services[0].loaded).to.be.false;
    });
    
    it('should handle unloading non-existent service', async () => {
      const result = await vramManager.unloadService('non-existent-service');
      
      expect(result.success).to.be.false;
      expect(result.error).to.include('not found');
    });
    
    it('should handle errors when unloading service', async () => {
      // Register a service
      await vramManager.registerService({
        service_name: 'test-service',
        service_url: 'http://localhost:8888',
        vram_usage_gb: 10
      });
      
      // Make axios.post throw an error
      axiosStub.rejects(new Error('Connection error'));
      
      // Unload the service
      const result = await vramManager.unloadService('test-service');
      
      expect(result.success).to.be.false;
      expect(result.error).to.include('Connection error');
    });
  });
  
  describe('Auto Unloading', () => {
    it('should auto-unload inactive services', async () => {
      // Set a short timeout for testing
      vramManager.setUnloadTimeout(1); // 1 minute
      
      // Register services with old last_used times
      await vramManager.registerService({
        service_name: 'inactive-service',
        service_url: 'http://localhost:8001',
        vram_usage_gb: 10,
        last_used: Date.now() - 120000 // 2 minutes ago
      });
      
      await vramManager.registerService({
        service_name: 'active-service',
        service_url: 'http://localhost:8002',
        vram_usage_gb: 10,
        last_used: Date.now() // Just now
      });
      
      // Run auto-unload
      const result = await vramManager.autoUnloadInactiveServices();
      
      expect(result.unloaded_services).to.be.an('array').that.includes('inactive-service');
      expect(result.unloaded_services).to.not.include('active-service');
      expect(result.freed_vram_gb).to.equal(10);
    });
  });
  
  describe('VRAM Limit Enforcement', () => {
    it('should enforce global VRAM limit', async () => {
      // Try to register a service that exceeds the VRAM limit
      const result = await vramManager.registerService({
        service_name: 'large-service',
        service_url: 'http://localhost:8888',
        vram_usage_gb: 70 // Exceeds 64GB limit
      });
      
      expect(result.success).to.be.false;
      expect(result.error).to.include('exceeds the maximum VRAM limit');
    });
    
    it('should enforce VRAM limit when requesting allocation', async () => {
      const result = await vramManager.requestVRAM({
        service_name: 'test-service',
        vram_needed_gb: 70, // Exceeds 64GB limit
        priority: 'high'
      });
      
      expect(result.success).to.be.false;
      expect(result.error).to.include('exceeds the maximum VRAM limit');
    });
  });
});
