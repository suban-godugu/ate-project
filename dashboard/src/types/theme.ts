export type Appearance = "dark" | "light" | "system";
export type PrimaryColor = "purple" | "blue" | "emerald" | "orange" | "red";
export type SidebarStyle = "default" | "compact" | "floating";
export type CardStyle = "glass" | "solid" | "minimal";
export type FontSize = "small" | "medium" | "large";
export type SidebarWidth = "compact" | "standard" | "expanded";
export type BorderRadius = "small" | "medium" | "large";
export type Density = "comfortable" | "compact";
export type DateFormat = "MM/DD/YYYY" | "DD/MM/YYYY" | "YYYY-MM-DD";
export type NumberFormat = "US" | "EU" | "IN";

export interface ThemeConfig {
  appearance: Appearance;
  primaryColor: PrimaryColor;
  sidebarStyle: SidebarStyle;
  cardStyle: CardStyle;
  fontSize: FontSize;
  compactMode: boolean;
  animations: boolean;
  sidebarWidth: SidebarWidth;
  borderRadius: BorderRadius;
  density: Density;
}

export interface ThemePreset {
  id: string;
  name: string;
  description: string;
  config: Partial<ThemeConfig>;
}

export interface AccountPreset {
  name: string;
  email: string;
  role: string;
  department: string;
  organization: string;
  lastLogin: string;
  defaultDashboard: string;
  language: string;
  timezone: string;
  dateFormat: DateFormat;
  numberFormat: NumberFormat;
  notifications: {
    email: boolean;
    push: boolean;
    desktop: boolean;
  };
}

export const defaultThemeConfig: ThemeConfig = {
  appearance: "dark",
  primaryColor: "purple",
  sidebarStyle: "default",
  cardStyle: "glass",
  fontSize: "medium",
  compactMode: false,
  animations: true,
  sidebarWidth: "standard",
  borderRadius: "medium",
  density: "comfortable",
};

export const themePresets: ThemePreset[] = [
  {
    id: "executive",
    name: "Executive",
    description: "Purple · Glass",
    config: {
      primaryColor: "purple",
      cardStyle: "glass",
      sidebarStyle: "default",
      appearance: "dark",
    },
  },
  {
    id: "corporate",
    name: "Corporate",
    description: "Blue · Solid",
    config: {
      primaryColor: "blue",
      cardStyle: "solid",
      sidebarStyle: "default",
      appearance: "dark",
    },
  },
  {
    id: "emerald",
    name: "Emerald",
    description: "Green · Glass",
    config: {
      primaryColor: "emerald",
      cardStyle: "glass",
      sidebarStyle: "floating",
      appearance: "dark",
    },
  },
  {
    id: "midnight",
    name: "Midnight",
    description: "Deep · Minimal",
    config: {
      primaryColor: "purple",
      cardStyle: "minimal",
      sidebarStyle: "compact",
      appearance: "dark",
      borderRadius: "small",
    },
  },
  {
    id: "high-contrast",
    name: "High Contrast",
    description: "Red · Bold",
    config: {
      primaryColor: "red",
      cardStyle: "solid",
      sidebarStyle: "default",
      appearance: "dark",
      animations: false,
    },
  },
];

export const defaultAccountPreset: AccountPreset = {
  name: "Alex Johnson",
  email: "alex@company.com",
  role: "Admin",
  department: "ATE Engineering",
  organization: "Synopsys Semiconductor",
  lastLogin: "Jun 29, 2026 · 08:42 AM",
  defaultDashboard: "Executive Dashboard",
  language: "English",
  timezone: "Asia/Kolkata",
  dateFormat: "MM/DD/YYYY",
  numberFormat: "US",
  notifications: {
    email: true,
    push: true,
    desktop: true,
  },
};

export const accentColors: {
  id: PrimaryColor;
  hex: string;
  label: string;
}[] = [
  { id: "purple", hex: "#7C3AED", label: "Purple" },
  { id: "blue", hex: "#2563EB", label: "Blue" },
  { id: "emerald", hex: "#059669", label: "Emerald" },
  { id: "orange", hex: "#EA580C", label: "Orange" },
  { id: "red", hex: "#DC2626", label: "Red" },
];
