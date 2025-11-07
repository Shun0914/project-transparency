export type Role = 'Member' | 'PM' | 'PL';

export const ROLE_LABELS: Record<Role, string> = {
  'Member': 'メンバー',
  'PM': 'PM',
  'PL': 'PL'
};

export const ROLE_WEIGHTS: Record<Role, number> = {
  'PL': 3,
  'PM': 2,
  'Member': 1
};

export const ROLE_COLORS: Record<Role, string> = {
  'PL': 'bg-purple-100 text-purple-800',
  'PM': 'bg-blue-100 text-blue-800',
  'Member': 'bg-gray-100 text-gray-800'
};
