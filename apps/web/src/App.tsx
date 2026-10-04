import { Suspense, lazy } from 'react';
import { Route, Routes } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { ToastViewport } from '@/components/ui/Toast';
import { SkeletonList } from '@/components/ui/Skeleton';

const Home = lazy(() => import('@/pages/Home'));
const Discover = lazy(() => import('@/pages/Discover'));
const Feed = lazy(() => import('@/pages/Feed'));
const ActivityDetail = lazy(() => import('@/pages/ActivityDetail'));
const CreateActivity = lazy(() => import('@/pages/CreateActivity'));
const Venues = lazy(() => import('@/pages/Venues'));
const VenueDetail = lazy(() => import('@/pages/VenueDetail'));
const VenueMap = lazy(() => import('@/pages/VenueMap'));
const Matchmaking = lazy(() => import('@/pages/Matchmaking'));
const Achievements = lazy(() => import('@/pages/Achievements'));
const Clubs = lazy(() => import('@/pages/Clubs'));
const ClubDetail = lazy(() => import('@/pages/ClubDetail'));
const Bookings = lazy(() => import('@/pages/Bookings'));
const Leaderboard = lazy(() => import('@/pages/Leaderboard'));
const People = lazy(() => import('@/pages/People'));
const Friends = lazy(() => import('@/pages/Friends'));
const Tournaments = lazy(() => import('@/pages/Tournaments'));
const TournamentDetail = lazy(() => import('@/pages/TournamentDetail'));
const Profile = lazy(() => import('@/pages/Profile'));
const Chat = lazy(() => import('@/pages/Chat'));
const Login = lazy(() => import('@/pages/Login'));
const Register = lazy(() => import('@/pages/Register'));
const ForgotPassword = lazy(() => import('@/pages/ForgotPassword'));
const ResetPassword = lazy(() => import('@/pages/ResetPassword'));
const VerifyEmail = lazy(() => import('@/pages/VerifyEmail'));
const NotFound = lazy(() => import('@/pages/NotFound'));

export default function App() {
  return (
    <>
      <AppShell>
        <Suspense fallback={<SkeletonList count={3} />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/discover" element={<Discover />} />
            <Route path="/feed" element={<Feed />} />
            <Route path="/activities/:id" element={<ActivityDetail />} />
            <Route path="/venues" element={<Venues />} />
            <Route path="/venues/:id" element={<VenueDetail />} />
            <Route path="/venue-map" element={<VenueMap />} />
            <Route path="/clubs" element={<Clubs />} />
            <Route path="/clubs/:id" element={<ClubDetail />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/people" element={<People />} />
            <Route path="/tournaments" element={<Tournaments />} />
            <Route path="/tournaments/:id" element={<TournamentDetail />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/verify-email" element={<VerifyEmail />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/matchmaking" element={<Matchmaking />} />
              <Route path="/achievements" element={<Achievements />} />
              <Route path="/create" element={<CreateActivity />} />
              <Route path="/bookings" element={<Bookings />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/friends" element={<Friends />} />
            </Route>

            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </AppShell>
      <ToastViewport />
    </>
  );
}
