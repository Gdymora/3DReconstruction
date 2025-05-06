import React, { useState, useEffect } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Divider,
  Grid,
  Typography,
  Paper,
  CircularProgress,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress
} from '@mui/material';
import {
  Download as DownloadIcon,
  ViewInAr as ViewIcon,
  CloudDownload as CloudDownloadIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import apiService from '../services/apiService';

const ResultsPage = () => {
  const { sessionId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [model, setModel] = useState(null);

  // Функція для отримання результатів
  const fetchResults = async () => {
    try {
      const response = await apiService.getResults(sessionId);

      if (response.status === 200) {
        setResults(response.data);
        
        // Якщо реконструкція завершена, отримуємо інформацію про модель
        if (response.data.status === 'completed') {
          try {
            const modelResponse = await apiService.getModelInfo(sessionId);
            if (modelResponse.status === 200) {
              setModel(modelResponse.data);
            }
          } catch (modelError) {
            console.error('Помилка завантаження інформації про модель:', modelError);
          }
        }
      } else {
        throw new Error('Неочікувана відповідь сервера');
      }
    } catch (err) {
      console.error('Помилка завантаження результатів:', err);
      setError(`Помилка завантаження результатів: ${err.response?.data?.error || err.message}`);
    } finally {
      setLoading(false); // Виходимо з режиму завантаження в будь-якому випадку
    }
  };

  // Початкове завантаження даних
  useEffect(() => {
    fetchResults();
  }, [sessionId]);

  // Періодичне оновлення статусу, якщо реконструкція в процесі
  useEffect(() => {
    let intervalId = null;
    
    if (results?.status === 'processing') {
      intervalId = setInterval(async () => {
        try {
          const statusResponse = await apiService.getReconstructionStatus(sessionId);
          if (statusResponse.status === 200) {
            setResults(prevResults => ({
              ...prevResults,
              ...statusResponse.data
            }));
            
            // Якщо процес завершено, очищаємо інтервал і оновлюємо дані
            if (statusResponse.data.status !== 'processing') {
              clearInterval(intervalId);
              
              // Повністю оновлюємо дані
              fetchResults();
            }
          }
        } catch (error) {
          console.error('Помилка при оновленні статусу:', error);
        }
      }, 3000); // Оновлюємо кожні 3 секунди
    }
    
    // Очищаємо інтервал при розмонтуванні компонента
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [results?.status, sessionId]);

  const handleDownloadFile = (url) => {
    window.open(url, '_blank');
  };

  const handleDownloadAll = () => {
    window.open(apiService.getDownloadZipUrl(sessionId), '_blank');
  };

  // Показуємо лоадер, поки дані завантажуються
  if (loading && !results) {
    return (
      <Container maxWidth="md" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h5">
          Завантаження результатів реконструкції...
        </Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>Помилка</AlertTitle>
          {error}
        </Alert>
        <Button
          component={RouterLink}
          to="/upload"
          variant="contained"
        >
          Спробувати знову
        </Button>
      </Container>
    );
  }

  if (!results) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="warning" sx={{ mb: 3 }}>
          <AlertTitle>Результати не знайдено</AlertTitle>
          Не вдалося знайти результати для цієї сесії.
        </Alert>
        <Button
          component={RouterLink}
          to="/upload"
          variant="contained"
        >
          Спробувати знову
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Typography
        variant="h4"
        component="h1"
        gutterBottom
        sx={{ mb: 4, textAlign: 'center', fontWeight: 'bold' }}
      >
        Результати 3D-реконструкції
      </Typography>

      {/* Статус реконструкції з індикатором прогресу */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {results.status === 'completed' ? (
            <CheckCircleIcon color="success" sx={{ fontSize: 30, mr: 1 }} />
          ) : results.status === 'failed' ? (
            <ErrorIcon color="error" sx={{ fontSize: 30, mr: 1 }} />
          ) : (
            <InfoIcon color="info" sx={{ fontSize: 30, mr: 1 }} />
          )}
          <Typography variant="h5">
            {results.status === 'completed'
              ? '3D-реконструкція успішно завершена'
              : results.status === 'failed'
                ? 'Реконструкція завершилася з помилками'
                : 'Реконструкція в процесі...'}
          </Typography>
        </Box>

        <Stack direction="row" spacing={1} sx={{ mb: 3 }}>
          <Chip
            label={`Якість: ${results.quality === 'low'
              ? 'низька'
              : results.quality === 'medium'
                ? 'середня'
                : 'висока'}`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`Метод: ${results.method === 'colmap'
              ? 'COLMAP'
              : results.method === 'openmvs'
                ? 'OpenMVS'
                : 'Нейронний'}`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`Зображень: ${results.num_images}`}
            color="primary"
            variant="outlined"
          />
        </Stack>

        {/* Додаємо індикатор прогресу, якщо статус "processing" */}
        {results.status === 'processing' && (
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="body1" sx={{ flexGrow: 1 }}>
                {results.current_message || 'Обробка даних...'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {results.progress || 0}%
              </Typography>
            </Box>
            
            <LinearProgress 
              variant="determinate" 
              value={results.progress || 0} 
              sx={{ height: 8, borderRadius: 4 }} 
            />
            
            {results.elapsed_time && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'right' }}>
                Минуло: {Math.floor(results.elapsed_time / 60)} хв {results.elapsed_time % 60} сек
              </Typography>
            )}
          </Box>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Button
              variant="contained"
              fullWidth
              startIcon={<ViewIcon />}
              component={RouterLink}
              to={`/view/${sessionId}`}
              size="large"
              sx={{ mb: { xs: 2, md: 0 } }}
              disabled={results.status === 'processing' || results.status === 'failed'}
            >
              Переглянути 3D-модель
            </Button>
          </Grid>
          <Grid item xs={12} md={6}>
            <Button
              variant="outlined"
              fullWidth
              startIcon={<CloudDownloadIcon />}
              onClick={handleDownloadAll}
              size="large"
              disabled={results.status === 'processing' || results.status === 'failed'}
            >
              Завантажити всі файли (ZIP)
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Доступні формати для завантаження */}
      {results.files && results.files.length > 0 && (
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Доступні формати для завантаження
          </Typography>

          <Grid container spacing={2}>
            {results.files.map((file, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      {file.filename}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {file.filename.endsWith('.obj') && 'Wavefront OBJ - для більшості 3D-редакторів'}
                      {file.filename.endsWith('.ply') && 'Stanford PLY - точкова хмара високої щільності'}
                      {file.filename.endsWith('.stl') && 'STL - для 3D-друку'}
                      {file.filename.endsWith('.glb') && 'GLB - бінарний формат для веб'}
                      {file.filename.endsWith('.gltf') && 'GLTF - для веб-переглядачів і AR'}
                    </Typography>
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      fullWidth
                      onClick={() => handleDownloadFile(file.url)}
                    >
                      Завантажити
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Технічна інформація */}
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Технічна інформація
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <InfoIcon />
                </ListItemIcon>
                <ListItemText
                  primary="ID сесії"
                  secondary={sessionId}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <InfoIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Дата створення"
                  secondary={new Date(results.timestamp * 1000).toLocaleString()}
                />
              </ListItem>
              {results.completed_at && (
                <ListItem>
                  <ListItemIcon>
                    <InfoIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Дата завершення"
                    secondary={new Date(results.completed_at * 1000).toLocaleString()}
                  />
                </ListItem>
              )}
            </List>
          </Grid>
          <Grid item xs={12} md={6}>
            <List dense>
              {model && (
                <>
                  <ListItem>
                    <ListItemIcon>
                      <InfoIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Тип моделі"
                      secondary={model.model_type.toUpperCase()}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <InfoIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="URL моделі"
                      secondary={model.model_url}
                    />
                  </ListItem>
                </>
              )}
            </List>
          </Grid>
        </Grid>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button
            component={RouterLink}
            to="/upload"
            variant="text"
          >
            Створити нову модель
          </Button>

          <Button
            component={RouterLink}
            to="/"
            variant="text"
            color="inherit"
          >
            На головну
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default ResultsPage;