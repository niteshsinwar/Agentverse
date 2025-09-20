import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Divider,
  Paper,
  Tooltip,
  Alert,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Folder as FolderIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Analytics as AnalyticsIcon,
  Timeline as TimelineIcon,
  Storage as StorageIcon,
  Computer as ServerIcon,
  PlayArrow as StartupIcon,
  History as HistoryIcon,
  Assessment as ReportIcon
} from '@mui/icons-material';

import LogViewer from './LogViewer';

interface LogSession {
  session_id: string;
  created_at: string;
  modified_at: string;
  has_events: boolean;
  has_readable_logs: boolean;
  events_size?: number;
  session_log_size?: number;
}

interface SessionSummary {
  session_id: string;
  total_events: number;
  start_time: string;
  end_time: string;
  event_counts: Record<string, number>;
  agent_activity: Record<string, number>;
  error_count: number;
  status: string;
}

const LogManagementPanel: React.FC = () => {
  const [sessions, setSessions] = useState<LogSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [summaryOpen, setSummaryOpen] = useState(false);
  const [currentSummary, setCurrentSummary] = useState<SessionSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [logType, setLogType] = useState<'session' | 'application' | 'startup'>('session');

  // Load sessions list
  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/logs/sessions');
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load session summary
  const fetchSessionSummary = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/v1/logs/sessions/${sessionId}/summary`);
      const summary = await response.json();
      setCurrentSummary(summary);
      setSummaryOpen(true);
    } catch (error) {
      console.error('Failed to fetch session summary:', error);
    }
  };

  // Delete session
  const deleteSession = async (sessionId: string) => {
    try {
      await fetch(`/api/v1/logs/sessions/${sessionId}`, { method: 'DELETE' });
      await fetchSessions(); // Refresh list
      setDeleteConfirmOpen(false);
      setSessionToDelete(null);
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  // Download session logs
  const downloadSession = async (sessionId: string, format: 'json' | 'zip' = 'zip') => {
    try {
      const response = await fetch(`/api/v1/logs/export/${sessionId}?format=${format}`);

      if (format === 'zip') {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `session_${sessionId}_logs.zip`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `session_${sessionId}_logs.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to download session:', error);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  // Format file size
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Get session status color
  const getSessionStatusColor = (session: LogSession): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    const now = new Date();
    const modified = new Date(session.modified_at);
    const hoursDiff = (now.getTime() - modified.getTime()) / (1000 * 60 * 60);

    if (hoursDiff < 1) return 'success'; // Recent activity
    if (hoursDiff < 24) return 'info'; // Within a day
    if (hoursDiff < 168) return 'warning'; // Within a week
    return 'default'; // Older
  };

  // Session Summary Dialog
  const SessionSummaryDialog = () => (
    <Dialog open={summaryOpen} onClose={() => setSummaryOpen(false)} maxWidth="md" fullWidth>
      <DialogTitle>
        <AnalyticsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Session Analytics: {currentSummary?.session_id}
      </DialogTitle>
      <DialogContent>
        {currentSummary && (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Alert severity={currentSummary.status === 'error' ? 'error' : 'success'}>
                Session Status: {currentSummary.status.toUpperCase()}
                {currentSummary.error_count > 0 && ` (${currentSummary.error_count} errors)`}
              </Alert>
            </Grid>

            <Grid item xs={6}>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Overview</Typography>
                <Typography>Total Events: {currentSummary.total_events}</Typography>
                <Typography>Start Time: {formatDate(currentSummary.start_time)}</Typography>
                <Typography>End Time: {formatDate(currentSummary.end_time)}</Typography>
              </Paper>
            </Grid>

            <Grid item xs={6}>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Event Types</Typography>
                {Object.entries(currentSummary.event_counts).map(([type, count]) => (
                  <Box key={type} display="flex" justifyContent="space-between">
                    <Typography variant="body2">{type}:</Typography>
                    <Chip label={count} size="small" />
                  </Box>
                ))}
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Agent Activity</Typography>
                <Grid container spacing={1}>
                  {Object.entries(currentSummary.agent_activity).map(([agent, count]) => (
                    <Grid item key={agent}>
                      <Chip
                        label={`${agent}: ${count}`}
                        color="primary"
                        variant="outlined"
                      />
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            </Grid>
          </Grid>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setSummaryOpen(false)}>Close</Button>
      </DialogActions>
    </Dialog>
  );

  // Delete Confirmation Dialog
  const DeleteConfirmDialog = () => (
    <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
      <DialogTitle>Confirm Deletion</DialogTitle>
      <DialogContent>
        <Typography>
          Are you sure you want to delete logs for session {sessionToDelete}?
          This action cannot be undone.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
        <Button
          onClick={() => sessionToDelete && deleteSession(sessionToDelete)}
          color="error"
          variant="contained"
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <StorageIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Log Management Center
      </Typography>

      {/* Log Type Selector */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Log Type</InputLabel>
                <Select value={logType} onChange={(e) => setLogType(e.target.value as any)} label="Log Type">
                  <MenuItem value="session">Session Logs</MenuItem>
                  <MenuItem value="application">Application Logs</MenuItem>
                  <MenuItem value="startup">Startup Logs</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={9}>
              <Box display="flex" gap={2}>
                <Button variant="outlined" startIcon={<ReportIcon />} onClick={fetchSessions}>
                  Refresh
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={() => {/* Implement bulk download */}}
                >
                  Export All
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {logType === 'session' && (
        <>
          {/* Sessions Overview */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <FolderIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h4">{sessions.length}</Typography>
                  <Typography color="text.secondary">Total Sessions</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <TimelineIcon sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                  <Typography variant="h4">
                    {sessions.filter(s => s.has_events).length}
                  </Typography>
                  <Typography color="text.secondary">With Events</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <HistoryIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                  <Typography variant="h4">
                    {sessions.filter(s => {
                      const hoursDiff = (new Date().getTime() - new Date(s.modified_at).getTime()) / (1000 * 60 * 60);
                      return hoursDiff < 24;
                    }).length}
                  </Typography>
                  <Typography color="text.secondary">Active Today</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <StorageIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                  <Typography variant="h4">
                    {formatFileSize(
                      sessions.reduce((total, s) => total + (s.events_size || 0) + (s.session_log_size || 0), 0)
                    )}
                  </Typography>
                  <Typography color="text.secondary">Total Size</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Sessions List */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Session Logs</Typography>
              {loading && <LinearProgress sx={{ mb: 2 }} />}

              <List>
                {sessions.map((session, index) => (
                  <React.Fragment key={session.session_id}>
                    <ListItem>
                      <ListItemIcon>
                        <FolderIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle1">
                              {session.session_id}
                            </Typography>
                            <Chip
                              label="Active"
                              size="small"
                              color={getSessionStatusColor(session)}
                            />
                            {session.has_events && (
                              <Chip label="Events" size="small" variant="outlined" />
                            )}
                            {session.has_readable_logs && (
                              <Chip label="Readable" size="small" variant="outlined" />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Created: {formatDate(session.created_at)}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Modified: {formatDate(session.modified_at)}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Size: {formatFileSize((session.events_size || 0) + (session.session_log_size || 0))}
                            </Typography>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Box display="flex" gap={1}>
                          <Tooltip title="View Logs">
                            <IconButton
                              onClick={() => {
                                setSelectedSession(session.session_id);
                                setViewerOpen(true);
                              }}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>

                          <Tooltip title="Analytics">
                            <IconButton
                              onClick={() => fetchSessionSummary(session.session_id)}
                            >
                              <AnalyticsIcon />
                            </IconButton>
                          </Tooltip>

                          <Tooltip title="Download">
                            <IconButton
                              onClick={() => downloadSession(session.session_id)}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>

                          <Tooltip title="Delete">
                            <IconButton
                              onClick={() => {
                                setSessionToDelete(session.session_id);
                                setDeleteConfirmOpen(true);
                              }}
                              color="error"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </ListItemSecondaryAction>
                    </ListItem>
                    {index < sessions.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>

              {sessions.length === 0 && !loading && (
                <Paper elevation={0} sx={{ p: 4, textAlign: 'center', bgcolor: 'grey.50' }}>
                  <FolderIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No log sessions found
                  </Typography>
                  <Typography color="text.secondary">
                    Session logs will appear here when agents are active.
                  </Typography>
                </Paper>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {logType === 'application' && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <ServerIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Application Logs
            </Typography>
            <LogViewer sessionId="application" />
          </CardContent>
        </Card>
      )}

      {logType === 'startup' && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <StartupIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Server Startup Logs
            </Typography>
            <LogViewer sessionId="startup" />
          </CardContent>
        </Card>
      )}

      {/* Log Viewer Dialog */}
      <Dialog open={viewerOpen} onClose={() => setViewerOpen(false)} maxWidth="xl" fullWidth>
        <DialogTitle>
          Log Viewer: {selectedSession}
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {selectedSession && <LogViewer sessionId={selectedSession} />}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewerOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Dialogs */}
      <SessionSummaryDialog />
      <DeleteConfirmDialog />
    </Box>
  );
};

export default LogManagementPanel;