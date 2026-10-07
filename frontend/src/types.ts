export interface Item {
  id: string;
  name: string;
  brand: string;
  model: string;
  category: string;
  description: string;
  purchaseDate: string;
  purchasePrice: number;
  purchaseChannel: string;
  serialNumber: string;
  warrantyMonths: number;
  warrantyEndDate: string | null;
  returnDeadline: string | null;
  returnWindowDays: number;
  status: string;
  coverImage: string;
  location: string;
  isDemo: boolean;
  createdAt: string;
  updatedAt: string;
  warrantyDaysLeft: number | null;
  nextMaintenance: string | null;
}
export interface Event {
  id: string;
  itemId: string;
  type: string;
  date: string;
  title: string;
  description: string;
  source: string;
  relatedId?: string;
}
export interface Maintenance {
  id: string;
  itemId: string;
  type: string;
  date: string;
  nextDueDate: string;
  intervalDays: number;
  description: string;
  cost: number;
}
export interface Repair {
  id: string;
  itemId: string;
  issue: string;
  reportDate: string;
  status: string;
  serviceType: string;
  cost: number;
  description: string;
  completionDate: string | null;
  progress: { status: string; date: string }[];
}
export interface Document {
  textStatus?: string;
  textSource?: string;
  ocrPageCount?: number;
  ocrError?: string;
  id: string;
  itemId: string;
  type: string;
  filename: string;
  filePath: string;
  extractedText: string;
  uploadedAt: string;
  originalFilename: string;
  storedFilename: string;
  mimeType: string;
  fileSize: number;
  sha256: string;
  pageCount: number | null;
  updatedAt: string;
}
export interface ItemImage {
  id: string;
  itemId: string;
  filePath: string;
  type: string;
  source: string;
  originalFilename: string;
  storedFilename: string;
  mimeType: string;
  fileSize: number;
  sha256: string;
  createdAt: string;
}
export interface DraftImage {
  id: string;
  draftId: string;
  originalFilename: string;
  storedFilename: string;
  filePath: string;
  mimeType: string;
  fileSize: number;
  type: string;
  sha256: string;
  createdAt: string;
}
export interface Consumption {
  id: string;
  consumableId: string;
  date: string;
  quantityUsed: number;
}
export interface Restock {
  id: string;
  consumableId: string;
  date: string;
  quantity: number;
  cost: number;
}
export interface Consumable {
  dataQuality?: string;
  estimateRange?: { minDays: number; maxDays: number; label: string } | null;
  qualityExplanation?: string;
  id: string;
  itemId: string;
  name: string;
  unit: string;
  currentStock: number;
  warningStock: number;
  coverImage: string;
  leadDays: number;
  estimatedDaysLeft: number | null;
  suggestedPurchaseDate: string | null;
  dailyRate: number | null;
  status: string;
  records: Consumption[];
  restocks: Restock[];
  method: string;
  createdAt: string;
  updatedAt: string;
}
export interface Reminder {
  id: string;
  itemId: string;
  type: string;
  title: string;
  dueDate: string;
  status: string;
  priority: string;
  relatedId: string;
  daysLeft: number;
}
export interface Candidate {
  field: string;
  value: string;
  confidence: number;
  sourceImage: string;
  rawText?: string;
}
export interface Recognition {
  sessionId: string;
  candidates: Candidate[];
  fields: Record<string, Candidate>;
  images: { filePath: string; type: string }[];
  mode: string;
  warnings: string[];
}
export interface Detail {
  item: Item;
  images: ItemImage[];
  events: Event[];
  documents: Document[];
  maintenance: Maintenance[];
  repairs: Repair[];
  consumables: Consumable[];
  suggestions: string[];
}
export interface Stats {
  itemCount: number;
  warrantyCount: number;
  maintenanceDue: number;
  consumableLow: number;
  warrantyCoverage: number;
  annualMaintenance: number;
  repairSpend: number;
  consumableSpend: number;
  monthlyConsumption: number;
  categories: { name: string; value: number }[];
  reminderTrend: { month: string; count: number; completed: number }[];
  maintenanceRanking: { name: string; count: number }[];
  warrantyDistribution: { name: string; count: number }[];
  consumableTrend: { month: string; cost: number }[];
  insights: string[];
}
export interface Snapshot {
  today: string;
  items: Item[];
  reminders: Reminder[];
  repairs: Repair[];
  consumables: Consumable[];
  stats: Stats;
}
