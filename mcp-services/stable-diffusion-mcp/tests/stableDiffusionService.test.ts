import { expect } from 'chai';
import { describe, it, beforeEach, afterEach } from 'mocha';
import sinon from 'sinon';
import { StableDiffusionService } from '../src/services/stableDiffusionService';
import * as fs from 'fs/promises';
import * as path from 'path';
import axios from 'axios';

describe('Stable Diffusion Service Tests', () => {
  let stableDiffusionService: StableDiffusionService;
  let fsStub: sinon.SinonStub;
  
  beforeEach(() => {
    // Create a fresh instance for each test
    stableDiffusionService = new StableDiffusionService();
    
    // Stub fs.writeFile to prevent actual file operations
    fsStub = sinon.stub(fs, 'writeFile');
    fsStub.resolves();
  });
  
  afterEach(() => {
    // Restore stubs after each test
    sinon.restore();
  });
  
  describe('Image Generation', () => {
    it('should generate images from text prompts', async () => {
      // Mock the internal image generation function
      const generateMock = sinon.stub(stableDiffusionService as any, 'generateImageInternal');
      generateMock.resolves({
        image_data: Buffer.from('mock image data'),
        width: 512,
        height: 512
      });
      
      const result = await stableDiffusionService.generateImage({
        prompt: 'A beautiful sunset over mountains',
        negative_prompt: 'blurry, low quality',
        width: 512,
        height: 512,
        num_inference_steps: 30,
        guidance_scale: 7.5
      });
      
      expect(result).to.have.property('image_path');
      expect(result).to.have.property('metadata');
      expect(result.metadata).to.have.property('width', 512);
      expect(result.metadata).to.have.property('height', 512);
      expect(result.metadata).to.have.property('prompt', 'A beautiful sunset over mountains');
    });
    
    it('should handle image generation errors', async () => {
      // Mock the internal image generation function to throw an error
      const generateMock = sinon.stub(stableDiffusionService as any, 'generateImageInternal');
      generateMock.rejects(new Error('Model loading error'));
      
      try {
        await stableDiffusionService.generateImage({
          prompt: 'A beautiful sunset over mountains',
          width: 512,
          height: 512
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('Model loading error');
      }
    });
    
    it('should respect image dimension limits', async () => {
      // Set max dimensions in the service
      (stableDiffusionService as any).maxImageWidth = 1024;
      (stableDiffusionService as any).maxImageHeight = 1024;
      
      // Mock the internal image generation function
      const generateMock = sinon.stub(stableDiffusionService as any, 'generateImageInternal');
      generateMock.resolves({
        image_data: Buffer.from('mock image data'),
        width: 1024,
        height: 1024
      });
      
      try {
        await stableDiffusionService.generateImage({
          prompt: 'A beautiful sunset over mountains',
          width: 2048, // Exceeds max width
          height: 1024
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('exceeds the maximum allowed');
      }
    });
  });
  
  describe('Image Variations', () => {
    it('should generate variations of existing images', async () => {
      // Mock fs.readFile to return mock image data
      const readFileStub = sinon.stub(fs, 'readFile');
      readFileStub.resolves(Buffer.from('mock image data'));
      
      // Mock the internal variation generation function
      const variationMock = sinon.stub(stableDiffusionService as any, 'generateVariationInternal');
      variationMock.resolves({
        image_data: Buffer.from('mock variation image data'),
        width: 512,
        height: 512
      });
      
      const result = await stableDiffusionService.generateImageVariation({
        image_path: '/path/to/source.jpg',
        prompt: 'Make it more vibrant',
        strength: 0.7,
        width: 512,
        height: 512
      });
      
      expect(result).to.have.property('image_path');
      expect(result).to.have.property('metadata');
      expect(result.metadata).to.have.property('source_image', '/path/to/source.jpg');
      expect(result.metadata).to.have.property('strength', 0.7);
    });
    
    it('should handle variation generation errors', async () => {
      // Mock fs.readFile to return mock image data
      const readFileStub = sinon.stub(fs, 'readFile');
      readFileStub.resolves(Buffer.from('mock image data'));
      
      // Mock the internal variation generation function to throw an error
      const variationMock = sinon.stub(stableDiffusionService as any, 'generateVariationInternal');
      variationMock.rejects(new Error('Variation generation error'));
      
      try {
        await stableDiffusionService.generateImageVariation({
          image_path: '/path/to/source.jpg',
          prompt: 'Make it more vibrant',
          strength: 0.7
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('Variation generation error');
      }
    });
    
    it('should validate strength parameter', async () => {
      try {
        await stableDiffusionService.generateImageVariation({
          image_path: '/path/to/source.jpg',
          prompt: 'Make it more vibrant',
          strength: 1.5 // Invalid: should be between 0 and 1
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('strength must be between 0 and 1');
      }
    });
  });
  
  describe('Image Inpainting', () => {
    it('should perform inpainting on images', async () => {
      // Mock fs.readFile to return mock image data
      const readFileStub = sinon.stub(fs, 'readFile');
      readFileStub.resolves(Buffer.from('mock image data'));
      
      // Mock the internal inpainting function
      const inpaintMock = sinon.stub(stableDiffusionService as any, 'inpaintImageInternal');
      inpaintMock.resolves({
        image_data: Buffer.from('mock inpainted image data'),
        width: 512,
        height: 512
      });
      
      const result = await stableDiffusionService.inpaintImage({
        image_path: '/path/to/source.jpg',
        mask_path: '/path/to/mask.jpg',
        prompt: 'Replace with a cat',
        width: 512,
        height: 512
      });
      
      expect(result).to.have.property('image_path');
      expect(result).to.have.property('metadata');
      expect(result.metadata).to.have.property('source_image', '/path/to/source.jpg');
      expect(result.metadata).to.have.property('mask_image', '/path/to/mask.jpg');
    });
    
    it('should handle inpainting errors', async () => {
      // Mock fs.readFile to return mock image data
      const readFileStub = sinon.stub(fs, 'readFile');
      readFileStub.resolves(Buffer.from('mock image data'));
      
      // Mock the internal inpainting function to throw an error
      const inpaintMock = sinon.stub(stableDiffusionService as any, 'inpaintImageInternal');
      inpaintMock.rejects(new Error('Inpainting error'));
      
      try {
        await stableDiffusionService.inpaintImage({
          image_path: '/path/to/source.jpg',
          mask_path: '/path/to/mask.jpg',
          prompt: 'Replace with a cat'
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).to.include('Inpainting error');
      }
    });
  });
  
  describe('Model Information', () => {
    it('should return model information', async () => {
      const modelInfo = await stableDiffusionService.getModelInfo();
      
      expect(modelInfo).to.have.property('model_id');
      expect(modelInfo).to.have.property('model_type', 'stable-diffusion');
      expect(modelInfo).to.have.property('capabilities');
      expect(modelInfo.capabilities).to.include('text-to-image');
    });
    
    it('should include quantization information', async () => {
      // Set 4-bit quantization flag
      (stableDiffusionService as any).enable4BitQuantization = true;
      
      const modelInfo = await stableDiffusionService.getModelInfo();
      
      expect(modelInfo).to.have.property('quantization');
      expect(modelInfo.quantization).to.equal('4-bit');
    });
  });
  
  describe('VRAM Management', () => {
    it('should report correct VRAM usage', () => {
      // Set VRAM usage in the service
      (stableDiffusionService as any).vramUsageGB = 16;
      
      const vramUsage = stableDiffusionService.getVRAMUsage();
      
      expect(vramUsage).to.have.property('vram_usage_gb');
      expect(vramUsage.vram_usage_gb).to.equal(16);
    });
    
    it('should unload model when requested', async () => {
      // Mock the internal unload function
      const unloadMock = sinon.stub(stableDiffusionService as any, 'unloadModelInternal');
      unloadMock.resolves(true);
      
      const result = await stableDiffusionService.unloadModel();
      
      expect(result.success).to.be.true;
      expect(result.model_unloaded).to.be.true;
      
      // Check that the model is marked as unloaded
      expect(stableDiffusionService.isModelLoaded()).to.be.false;
    });
    
    it('should reload model after unloading', async () => {
      // First unload the model
      (stableDiffusionService as any).modelLoaded = false;
      
      // Mock the internal load function
      const loadMock = sinon.stub(stableDiffusionService as any, 'loadModelInternal');
      loadMock.resolves(true);
      
      // Mock the internal image generation function
      const generateMock = sinon.stub(stableDiffusionService as any, 'generateImageInternal');
      generateMock.resolves({
        image_data: Buffer.from('mock image data'),
        width: 512,
        height: 512
      });
      
      // Generate an image, which should reload the model
      await stableDiffusionService.generateImage({
        prompt: 'This should reload the model',
        width: 512,
        height: 512
      });
      
      expect(loadMock.calledOnce).to.be.true;
      expect(stableDiffusionService.isModelLoaded()).to.be.true;
    });
    
    it('should optimize VRAM usage with 4-bit quantization', async () => {
      // Set 4-bit quantization flag
      (stableDiffusionService as any).enable4BitQuantization = true;
      
      // Mock the internal load function
      const loadMock = sinon.stub(stableDiffusionService as any, 'loadModelInternal');
      loadMock.resolves(true);
      
      // Force model reload
      (stableDiffusionService as any).modelLoaded = false;
      await (stableDiffusionService as any).loadModel();
      
      // Check that the load function was called with quantization parameter
      expect(loadMock.calledOnce).to.be.true;
      expect(loadMock.firstCall.args[0]).to.have.property('quantization', '4bit');
    });
  });
  
  describe('Performance Benchmarks', () => {
    it('should generate images within acceptable time', async () => {
      // Mock the internal image generation function with a fast response
      const generateMock = sinon.stub(stableDiffusionService as any, 'generateImageInternal');
      generateMock.resolves({
        image_data: Buffer.from('mock image data'),
        width: 512,
        height: 512
      });
      
      const startTime = Date.now();
      await stableDiffusionService.generateImage({
        prompt: 'Performance test image',
        width: 512,
        height: 512
      });
      const endTime = Date.now();
      
      const executionTime = endTime - startTime;
      expect(executionTime).to.be.lessThan(1000); // Less than 1 second in test environment
    });
  });
  
  describe('Integration with MCP Manager', () => {
    it('should register with MCP Manager on startup', async () => {
      // Mock axios post method
      const axiosPostStub = sinon.stub(axios, 'post');
      axiosPostStub.resolves({ data: { success: true } });
      
      // Call the register method
      await (stableDiffusionService as any).registerWithMCPManager();
      
      // Check that the registration request was made
      expect(axiosPostStub.calledOnce).to.be.true;
      const registrationData = axiosPostStub.firstCall.args[1];
      expect(registrationData).to.have.property('service_name');
      expect(registrationData).to.have.property('service_url');
      expect(registrationData).to.have.property('vram_usage_gb');
    });
    
    it('should handle MCP Manager registration errors', async () => {
      // Mock axios post method to fail
      const axiosPostStub = sinon.stub(axios, 'post');
      axiosPostStub.rejects(new Error('Connection error'));
      
      // Mock console.error to prevent actual logging
      const consoleErrorStub = sinon.stub(console, 'error');
      
      // Call the register method
      await (stableDiffusionService as any).registerWithMCPManager();
      
      // Check that the error was logged
      expect(consoleErrorStub.calledOnce).to.be.true;
      expect(consoleErrorStub.firstCall.args[0]).to.include('Failed to register with MCP Manager');
    });
  });
});
