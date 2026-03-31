import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from './ui/Button';
import Modal from './ui/Modal';
import { UserRound, AtSign, ShieldCheck, Timer, CalendarDays, Zap, TrendingUp, BadgeCheck, AlertCircle, Loader } from 'lucide-react';
import { usersAPI } from '../services/api';

interface UserAnalysisStats {
  total_analyses: number;
  pending_analyses: number;
  in_progress_analyses: number;
  completed_analyses: number;
  average_risk_score: number | null;
}

interface UserDetailedProfile {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_online: boolean;
  created_at: string;
  last_login: string | null;
  previous_login: string | null;
  session_start: string | null;
  total_online_time: number;
  analysis_stats: UserAnalysisStats;
}

interface UserProfileProps {
  userId: number;
  isOpen: boolean;
  onClose: () => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ userId, isOpen, onClose }) => {
  const { t, i18n } = useTranslation();
  const [profile, setProfile] = useState<UserDetailedProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && userId) {
      fetchUserProfile();
    }
  }, [isOpen, userId]);

  const fetchUserProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await usersAPI.getProfile(userId);
      setProfile(data);
    } catch (err) {
      setError(t('userProfile.networkError') || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return t('userProfile.never') || 'Never';
    const date = new Date(dateString);
    return date.toLocaleString(i18n.language === 'ru' ? 'ru-RU' : 'en-US');
  };

  const formatOnlineTime = (seconds: number) => {
    if (seconds === 0) return t('userProfile.noData') || 'No data';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    return `${hours}${t('userProfile.hours')} ${minutes}${t('userProfile.minutes')}`;
  };

  const getRoleLabel = (role: string) => {
    return t(`userManagement.roles.${role}`) || role;
  };

  const getRiskScoreColor = (score: number | null): React.CSSProperties => {
    if (score === null) return { color: 'var(--text-muted)' };
    if (score <= 3) return { color: 'var(--success)' };
    if (score <= 6) return { color: '#f9ab00' };
    return { color: 'var(--danger)' };
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t('userProfile.title') || 'User Profile'}>
      {loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader className="w-12 h-12 animate-spin mb-4" style={{ color: 'var(--accent)' }} />
          <p style={{ color: 'var(--text-muted)' }}>{t('userProfile.loading') || 'Loading...'}</p>
        </div>
      )}

      {error && (
        <div
          className="px-4 py-3 rounded-xl flex items-center gap-3 mb-4 border"
          style={{ background: 'var(--danger-bg)', borderColor: 'var(--danger)', color: 'var(--danger)' }}
        >
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {profile && !loading && (
        <div className="space-y-6">
          {/* User Header */}
          <div
            className="relative backdrop-blur-xl rounded-2xl p-6 border shadow-sm"
            style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
          >
            <div className="flex items-center gap-4">
              <div
                className="p-4 rounded-2xl shadow-sm"
                style={{ background: 'var(--accent)' }}
              >
                <UserRound className="w-10 h-10 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-semibold mb-1" style={{ color: 'var(--text)' }}>
                  {profile.full_name}
                </h2>
                <p className="text-sm flex items-center gap-2" style={{ color: 'var(--text-muted)' }}>
                  <AtSign className="w-4 h-4" />
                  {profile.email}
                </p>
              </div>
              <div>
                <span
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium backdrop-blur-xl border"
                  style={
                    profile.is_online
                      ? { background: 'var(--success-bg)', color: 'var(--success)', borderColor: 'rgba(26,115,232,0.3)' }
                      : { background: 'var(--bg-secondary)', color: 'var(--text-muted)', borderColor: 'var(--card-border)' }
                  }
                >
                  <span
                    className={`w-2 h-2 rounded-full ${profile.is_online ? 'animate-pulse' : ''}`}
                    style={{ background: profile.is_online ? 'var(--success)' : 'var(--text-muted)' }}
                  ></span>
                  {profile.is_online
                    ? (t('userManagement.online') || 'Online')
                    : (t('userManagement.offline') || 'Offline')
                  }
                </span>
              </div>
            </div>
          </div>

          {/* Basic Information */}
          <div className="grid grid-cols-2 gap-4">
            <div
              className="relative backdrop-blur-xl rounded-2xl p-4 border shadow-sm transition-all duration-500 hover:shadow-md"
              style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="p-2 rounded-xl shadow-sm"
                  style={{ background: 'var(--accent)' }}
                >
                  <ShieldCheck className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.role') || 'Role'}
                  </p>
                  <p className="font-semibold" style={{ color: 'var(--text)' }}>{getRoleLabel(profile.role)}</p>
                </div>
              </div>
            </div>

            <div
              className="relative backdrop-blur-xl rounded-2xl p-4 border shadow-sm transition-all duration-500 hover:shadow-md"
              style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="p-2 rounded-xl shadow-sm"
                  style={{ background: 'var(--accent)' }}
                >
                  <CalendarDays className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.registrationDate') || 'Registration Date'}
                  </p>
                  <p className="font-semibold text-sm" style={{ color: 'var(--text)' }}>{formatDate(profile.created_at)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Activity Information */}
          <div
            className="relative backdrop-blur-xl rounded-2xl p-6 border shadow-sm transition-all duration-500 hover:shadow-md"
            style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div
                className="p-2 rounded-xl shadow-sm"
                style={{ background: 'var(--success)' }}
              >
                <Zap className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
                {t('userProfile.activityHistory') || 'Activity History'}
              </h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div
                className="p-4 rounded-xl border"
                style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Timer className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                  <p className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.currentLogin') || 'Current Login'}
                  </p>
                </div>
                <p className="font-semibold text-sm" style={{ color: 'var(--text)' }}>{formatDate(profile.last_login)}</p>
              </div>
              <div
                className="p-4 rounded-xl border"
                style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Timer className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                  <p className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.previousLogin') || 'Previous Login'}
                  </p>
                </div>
                <p className="font-semibold text-sm" style={{ color: 'var(--text)' }}>{formatDate(profile.previous_login)}</p>
              </div>
              <div
                className="p-4 rounded-xl border"
                style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <CalendarDays className="w-4 h-4" style={{ color: '#f9ab00' }} />
                  <p className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.sessionStart') || 'Session Start'}
                  </p>
                </div>
                <p className="font-semibold text-sm" style={{ color: 'var(--text)' }}>{formatDate(profile.session_start)}</p>
              </div>
              <div
                className="p-4 rounded-xl border"
                style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4" style={{ color: 'var(--success)' }} />
                  <p className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.totalOnlineTime') || 'Total Online Time'}
                  </p>
                </div>
                <p className="font-semibold text-sm" style={{ color: 'var(--text)' }}>{formatOnlineTime(profile.total_online_time)}</p>
              </div>
            </div>
          </div>

          {/* Analysis Statistics */}
          <div
            className="relative backdrop-blur-xl rounded-2xl p-6 border shadow-sm transition-all duration-500 hover:shadow-md"
            style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div
                className="p-2 rounded-xl shadow-sm"
                style={{ background: 'var(--accent)' }}
              >
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
                {t('userProfile.analysisStats') || 'Analysis Statistics'}
              </h3>
            </div>

            {/* Total Analyses and Average Risk Score */}
            <div
              className="mb-6 p-6 rounded-xl border"
              style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.totalAnalyses') || 'Total Analyses'}
                  </p>
                  <p className="text-4xl font-bold" style={{ color: 'var(--accent)' }}>
                    {profile.analysis_stats.total_analyses}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.avgRiskScore') || 'Average Risk Score'}
                  </p>
                  <p className="text-4xl font-bold" style={getRiskScoreColor(profile.analysis_stats.average_risk_score)}>
                    {profile.analysis_stats.average_risk_score !== null
                      ? `${profile.analysis_stats.average_risk_score}`
                      : (t('userProfile.noData') || 'N/A')
                    }
                  </p>
                  {profile.analysis_stats.average_risk_score !== null && (
                    <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>/ 10</p>
                  )}
                </div>
              </div>
            </div>

            {/* Status Cards Grid */}
            <div className="grid grid-cols-3 gap-4">
              <div
                className="relative p-4 rounded-xl border transition-all duration-300 hover:shadow-md"
                style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <BadgeCheck className="w-5 h-5" style={{ color: 'var(--success)' }} />
                  <p className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.completed') || 'Completed'}
                  </p>
                </div>
                <p className="text-3xl font-bold" style={{ color: 'var(--success)' }}>
                  {profile.analysis_stats.completed_analyses}
                </p>
              </div>

              <div
                className="relative p-4 rounded-xl border transition-all duration-300 hover:shadow-md"
                style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <Loader className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                  <p className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.inProgress') || 'In Progress'}
                  </p>
                </div>
                <p className="text-3xl font-bold" style={{ color: 'var(--accent)' }}>
                  {profile.analysis_stats.in_progress_analyses}
                </p>
              </div>

              <div
                className="relative p-4 rounded-xl border transition-all duration-300 hover:shadow-md"
                style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <Timer className="w-5 h-5" style={{ color: '#f9ab00' }} />
                  <p className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
                    {t('userProfile.pending') || 'Pending'}
                  </p>
                </div>
                <p className="text-3xl font-bold" style={{ color: '#f9ab00' }}>
                  {profile.analysis_stats.pending_analyses}
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <Button onClick={onClose}>
              {t('userProfile.close') || 'Close'}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default UserProfile;
