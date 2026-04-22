export const colors = {
  // Core sunflower palette
  primary: '#F5C518',        // sunflower yellow
  primaryDark: '#D4A800',    // darker yellow for pressed states
  primaryLight: '#FFF3B0',   // pale yellow for highlights

  // Backgrounds
  background: '#FFFDF0',     // warm cream
  card: '#FFFFFF',
  inputBg: '#F9F6E8',

  // Text
  text: '#2C2200',           // deep warm brown
  textSecondary: '#7A6A30',
  textMuted: '#B0A060',
  textOnPrimary: '#2C2200',

  // Accents
  green: '#4A7C3F',          // leaf green for success/health
  greenLight: '#E8F5E2',
  crisis: '#C0392B',
  crisisLight: '#FDECEA',

  // Borders & dividers
  border: '#EDE8CC',
  divider: '#F0EAD0',

  // Chat bubbles
  bubbleUser: '#F5C518',
  bubbleUserText: '#2C2200',
  bubbleAI: '#FFFFFF',
  bubbleAIText: '#2C2200',
  bubbleAIBorder: '#EDE8CC',

  // Tab bar
  tabActive: '#D4A800',
  tabInactive: '#B0A060',
  tabBackground: '#FFFDF0',

  white: '#FFFFFF',
  shadow: 'rgba(100, 80, 0, 0.08)',
};

export const typography = {
  fontSizeXS: 11,
  fontSizeSM: 13,
  fontSizeMD: 15,
  fontSizeLG: 17,
  fontSizeXL: 20,
  fontSizeXXL: 26,

  fontWeightNormal: '400' as const,
  fontWeightMedium: '500' as const,
  fontWeightSemiBold: '600' as const,
  fontWeightBold: '700' as const,
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const radius = {
  sm: 8,
  md: 14,
  lg: 20,
  full: 999,
};
