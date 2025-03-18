// Using Node.js built-in modules
import { exec as execCallback } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as fsSync from 'fs';
import * as path from 'path';
import si from 'systeminformation';

// Fix execAsync reference
const execAsync = promisify(execCallback);

// Add Node.js types
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      MAX_VRAM_USAGE_GB?: string;
      VRAM_RESERVE_GB?: string;
      ENABLE_AUTO_UNLOAD?: string;
      UNLOAD_TIMEOUT_MINUTES?: string;
      SERVICES_CONFIG_PATH?: string;
    }
  }
}

interface ModelInfo {
  name: string;
  vramUsageGb: number;
  lastUsed: Date;
}

interface ServiceInfo {
  name: string;
  url: string;
  models: ModelInfo[];
  usedVramGb: number;
}

interface VRAMStatus {
  totalVramGb: number;
  usedVramGb: number;
  availableVramGb: number;
  services: {
    name: string;
    usedVramGb: number;
    models: string[];
  }[];
}

interface UnloadModelResult {
  success: boolean;
  freedVramGb: number;
  message: string;
}

interface RegisterServiceResult {
  success: boolean;
  message: string;
}

export class VRAMManager {
  private services: Map<string, ServiceInfo> = new Map();
  private maxVramUsageGb: number;
  private vramReserveGb: number;
  private enableAutoUnload: boolean;
  private unloadTimeoutMinutes: number;
  private servicesConfigPath: string;
  private totalVramGb: number = 0;

  constructor() {
    // Load configuration from environment variables
    this.maxVramUsageGb = parseFloat(process.env.MAX_VRAM_USAGE_GB || '60');
    this.vramReserveGb = parseFloat(process.env.VRAM_RESERVE_GB || '4');
    this.enableAutoUnload = process.env.ENABLE_AUTO_UNLOAD !== 'false';
    this.unloadTimeoutMinutes = parseFloat(process.env.UNLOAD_TIMEOUT_MINUTES || '30');
    this.servicesConfigPath = process.env.SERVICES_CONFIG_PATH || './services.json';

    // Initialize services from config file if it exists
    this.loadServicesFromConfig();

    // Start auto-unload timer if enabled
    if (this.enableAutoUnload) {
      setInterval(() => this.autoUnloadInactiveModels(), 60000); // Check every minute
    }

    // Get total VRAM
    this.updateTotalVram();
  }

  private async updateTotalVram(): Promise<void> {
    try {
      const gpuData = await si.graphics();
      if (gpuData && gpuData.controllers && gpuData.controllers.length > 0) {
        // Sum up VRAM across all GPUs
        this.totalVramGb = gpuData.controllers.reduce((total, gpu) => {
          // Convert to GB and add to total (handle null vram values)
          return total + ((gpu.vram || 0) / 1024);
        }, 0);
      } else {
        // Fallback to default if no GPU data available
        this.totalVramGb = 64; // Default to 64GB
        console.warn('No GPU data available, using default 64GB VRAM');
      }
    } catch (error) {
      console.error('Error getting GPU information:', error);
      this.totalVramGb = 64; // Default to 64GB
    }
  }

  private loadServicesFromConfig(): void {
    try {
      if (fsSync.existsSync(this.servicesConfigPath)) {
        const configData = fsSync.readFileSync(this.servicesConfigPath, 'utf8');
        const servicesConfig = JSON.parse(configData);
        
        for (const service of servicesConfig) {
          this.services.set(service.name, {
            name: service.name,
            url: service.url,
            models: service.models.map((model: any) => ({
              name: model.name,
              vramUsageGb: model.vramUsageGb,
              lastUsed: new Date()
            })),
            usedVramGb: service.models.reduce((total: number, model: any) => total + model.vramUsageGb, 0)
          });
        }
        
        console.log(`Loaded ${this.services.size} services from config`);
      }
    } catch (error) {
      console.error('Error loading services config:', error);
    }
  }

  private saveServicesToConfig(): void {
    try {
      const servicesConfig = Array.from(this.services.values()).map(service => ({
        name: service.name,
        url: service.url,
        models: service.models.map(model => ({
          name: model.name,
          vramUsageGb: model.vramUsageGb
        }))
      }));
      
      const configDir = path.dirname(this.servicesConfigPath);
      if (!fsSync.existsSync(configDir)) {
        fsSync.mkdirSync(configDir, { recursive: true });
      }
      
      fsSync.writeFileSync(this.servicesConfigPath, JSON.stringify(servicesConfig, null, 2), 'utf8');
      console.log(`Saved ${this.services.size} services to config`);
    } catch (error) {
      console.error('Error saving services config:', error);
    }
  }

  private autoUnloadInactiveModels(): void {
    const now = new Date();
    let unloadedModels = 0;
    
    for (const service of this.services.values()) {
      for (const model of service.models) {
        const minutesSinceLastUse = (now.getTime() - model.lastUsed.getTime()) / (1000 * 60);
        
        if (minutesSinceLastUse > this.unloadTimeoutMinutes) {
          // Unload the model
          this.unloadModelInternal(model.name, service.name);
          unloadedModels++;
        }
      }
    }
    
    if (unloadedModels > 0) {
      console.log(`Auto-unloaded ${unloadedModels} inactive models`);
    }
  }

  private async unloadModelInternal(modelName: string, serviceName: string): Promise<UnloadModelResult> {
    const service = this.services.get(serviceName);
    
    if (!service) {
      return {
        success: false,
        freedVramGb: 0,
        message: `Service ${serviceName} not found`
      };
    }
    
    const modelIndex = service.models.findIndex(model => model.name === modelName);
    
    if (modelIndex === -1) {
      return {
        success: false,
        freedVramGb: 0,
        message: `Model ${modelName} not found in service ${serviceName}`
      };
    }
    
    const model = service.models[modelIndex];
    const freedVramGb = model.vramUsageGb;
    
    // Remove the model from the service
    service.models.splice(modelIndex, 1);
    service.usedVramGb -= freedVramGb;
    
    // Update the service in the map
    this.services.set(serviceName, service);
    
    // Save the updated services to config
    this.saveServicesToConfig();
    
    // Try to send unload command to the service
    try {
      const response = await fetch(`${service.url}/models/unload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ model_name: modelName })
      });
      
      if (!response.ok) {
        console.warn(`Failed to send unload command to service ${serviceName}: ${response.statusText}`);
      }
    } catch (error) {
      console.warn(`Error sending unload command to service ${serviceName}:`, error);
    }
    
    return {
      success: true,
      freedVramGb,
      message: `Model ${modelName} unloaded successfully`
    };
  }

  public async getVRAMStatus(): Promise<VRAMStatus> {
    // Update total VRAM
    await this.updateTotalVram();
    
    // Calculate total used VRAM
    const usedVramGb = Array.from(this.services.values()).reduce(
      (total, service) => total + service.usedVramGb, 0
    );
    
    // Calculate available VRAM
    const availableVramGb = Math.max(0, this.totalVramGb - usedVramGb - this.vramReserveGb);
    
    // Build service status list
    const serviceStatus = Array.from(this.services.values()).map(service => ({
      name: service.name,
      usedVramGb: service.usedVramGb,
      models: service.models.map(model => model.name)
    }));
    
    return {
      totalVramGb: this.totalVramGb,
      usedVramGb,
      availableVramGb,
      services: serviceStatus
    };
  }

  public async unloadModel(modelName: string, serviceName: string): Promise<UnloadModelResult> {
    return this.unloadModelInternal(modelName, serviceName);
  }

  public async registerService(
    serviceName: string, 
    serviceUrl: string, 
    models: { name: string; vramUsageGb: number }[]
  ): Promise<RegisterServiceResult> {
    // Calculate total VRAM usage for this service
    const serviceVramUsage = models.reduce((total, model) => total + model.vramUsageGb, 0);
    
    // Check if we have enough VRAM available
    const status = await this.getVRAMStatus();
    
    if (serviceVramUsage > status.availableVramGb) {
      return {
        success: false,
        message: `Not enough VRAM available. Required: ${serviceVramUsage}GB, Available: ${status.availableVramGb}GB`
      };
    }
    
    // Create service info
    const serviceInfo: ServiceInfo = {
      name: serviceName,
      url: serviceUrl,
      models: models.map(model => ({
        name: model.name,
        vramUsageGb: model.vramUsageGb,
        lastUsed: new Date()
      })),
      usedVramGb: serviceVramUsage
    };
    
    // Add or update the service
    this.services.set(serviceName, serviceInfo);
    
    // Save the updated services to config
    this.saveServicesToConfig();
    
    return {
      success: true,
      message: `Service ${serviceName} registered successfully`
    };
  }

  public async updateModelUsage(modelName: string, serviceName: string): Promise<boolean> {
    const service = this.services.get(serviceName);
    
    if (!service) {
      return false;
    }
    
    const model = service.models.find(model => model.name === modelName);
    
    if (!model) {
      return false;
    }
    
    // Update last used timestamp
    model.lastUsed = new Date();
    return true;
  }

  public async getServiceList(): Promise<{ name: string; url: string }[]> {
    return Array.from(this.services.values()).map(service => ({
      name: service.name,
      url: service.url
    }));
  }
}
