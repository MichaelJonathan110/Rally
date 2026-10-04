import {
  Home,
  Compass,
  PlusCircle,
  MessageSquare,
  User,
  MapPin,
  Users,
  CalendarCheck,
  Trophy,
  Swords,
  Flame,
  Sparkles,
  Award,
  Map,
} from 'lucide-react';

export interface NavItem {
  to: string;
  label: string;
  icon: typeof Home;
  primary?: boolean;
}

/** Mobile bottom bar - the five destinations a player uses every day. */
export const PRIMARY_NAV: NavItem[] = [
  { to: '/', label: 'Beranda', icon: Home, primary: true },
  { to: '/discover', label: 'Jelajah', icon: Compass, primary: true },
  { to: '/create', label: 'Buat', icon: PlusCircle, primary: true },
  { to: '/feed', label: 'Feed', icon: Flame, primary: true },
  { to: '/profile', label: 'Profil', icon: User, primary: true },
];

/** Desktop sidebar - everything else, grouped by intent. */
export const SECONDARY_NAV: NavItem[] = [
  { to: '/matchmaking', label: 'Cocok Untukmu', icon: Sparkles },
  { to: '/people', label: 'Orang & MMR', icon: Users },
  { to: '/friends', label: 'Teman', icon: Users },
  { to: '/leaderboard', label: 'Peringkat', icon: Trophy },
  { to: '/achievements', label: 'Pencapaian', icon: Award },
  { to: '/tournaments', label: 'Turnamen', icon: Swords },
  { to: '/venues', label: 'Venue', icon: MapPin },
  { to: '/venue-map', label: 'Peta Venue', icon: Map },
  { to: '/clubs', label: 'Komunitas', icon: Users },
  { to: '/bookings', label: 'Booking', icon: CalendarCheck },
  { to: '/chat', label: 'Obrolan', icon: MessageSquare },
];
