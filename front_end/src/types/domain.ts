// src/types/domain.ts

// --- ENUMS & CONSTANTS ---

export type HealthStatus = 'EXCELLENT' | 'GOOD' | 'WARNING' | 'CRITICAL';
export type InterventionPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
export type InterventionType = 'ARROSAGE' | 'TAILLE' | 'FERTILISATION' | 'REPARATION' | 'NETTOYAGE';

// --- ENTITÉS PRINCIPALES ---

export interface User {
  id: string;
  name: string;
  role: 'MANAGER' | 'TECHNICIAN' | 'ADMIN';
  avatarUrl?: string;
}

export interface EspaceVert {
  id: string;
  name: string;
  city: string;
  zipCode: string;
  coordinates: { lat: number; lng: number };
  surface: number; // en m²
  type: 'JARDIN' | 'PARC' | 'TOIT_VEGETALISE' | 'ROND_POINT';
  healthStatus: HealthStatus;
  waterLevel: number; // pourcentage humidité sol
  lastInterventionDate?: string;
}

export interface Intervention {
  id: string;
  espaceId: string;
  type: InterventionType;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED';
  priority: InterventionPriority;
  scheduledDate: string;
  description?: string;
  assignedTo?: string; // ID du technicien
}

export interface WeatherData {
  city: string;
  temp: number;
  condition: 'SUNNY' | 'CLOUDY' | 'RAINY' | 'STORM';
  humidity: number;
  windSpeed: number;
}

// --- DASHBOARD SPECIFIC ---

export interface GlobalKPIs {
  healthIndex: number; // 0-100 (Moyenne pondérée)
  activeAlertsCount: number; // Nombre de sites nécessitant intervention
  airQuality: number; // CO2 ppm moyen
  waterConsumption: number; // Litres ou % global
  trend: 'UP' | 'DOWN' | 'STABLE';
}

export interface ZonePerformance {
  zoneName: string; // ex: "Lyon-Est"
  totalSpaces: number;
  healthScore: number; // 0-100
  alertCount: number;
}