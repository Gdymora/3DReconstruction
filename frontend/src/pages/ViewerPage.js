import React, { useState, useEffect, useRef, Suspense } from "react";
import { useParams, Link as RouterLink } from "react-router-dom";
import {
  Box,
  Button,
  Container,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  AlertTitle,
  Slider,
  Stack,
  FormControlLabel,
  Switch,
  Tooltip,
  IconButton,
  Divider,
} from "@mui/material";
import {
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  Download as DownloadIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Refresh as RefreshIcon,
  ArrowBack as ArrowBackIcon,
} from "@mui/icons-material";
import { Canvas } from "@react-three/fiber";
import {
  OrbitControls,
  PerspectiveCamera,
  Environment,
  useGLTF,
  Html,
  useProgress,
  Grid as ThreeGrid,
} from "@react-three/drei";
import { toast } from "react-toastify";
import apiService from "../services/apiService"; // ⚠️ переконайся, що шлях правильний

// Компонент завантаження для Three.js
const Loader = () => {
  const { progress } = useProgress();
  return (
    <Html center>
      <Box sx={{ textAlign: "center", color: "white" }}>
        <CircularProgress size={60} sx={{ mb: 1 }} />
        <Typography variant="h6">{progress.toFixed(0)}%</Typography>
      </Box>
    </Html>
  );
};

// Компонент моделі без умовного виклику хуків
const Model = ({ url, modelType }) => {
  console.log("Завантаження моделі з URL:", url); // Логування URL

  // Хук useGLTF завжди викликається на верхньому рівні
  const { scene } = useGLTF(url, true); // true включає відладку

  // Хук useEffect також завжди викликається на верхньому рівні
  useEffect(() => {
    return () => {
      useGLTF.preload(url);
    };
  }, [url]);

  // Відображення помилок можна зробити всередині компонента ErrorBoundary
  return <primitive object={scene} dispose={null} />;
};

const ViewerPage = () => {
  const { sessionId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [model, setModel] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [gridSize, ] = useState(10);
  const [zoom, setZoom] = useState(2);
  const [autoRotate, setAutoRotate] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const fetchModel = async () => {
      try {
        const response = await apiService.getModelInfo(sessionId);
        console.log("Отримано інформацію про модель:", response.data);

        if (response.data && response.data.model_url) {
          // Перевірка і коригування URL
          let modelUrl = response.data.model_url;
          if (!modelUrl.startsWith("http")) {
            modelUrl = `http://localhost:5000${modelUrl}`;
          }

          console.log("Повний URL моделі:", modelUrl);

          // Оновлення стану з коректним URL
          setModel({
            ...response.data,
            model_url: modelUrl,
          });
        } else {
          setError("Отримано невірні дані моделі від сервера");
        }
      } catch (err) {
        console.error("Помилка завантаження інформації про модель:", err);
        setError(
          `Помилка завантаження інформації про модель: ${
            err.response?.data?.error || err.message
          }`
        );
        toast.error(
          `Помилка завантаження інформації про модель: ${
            err.response?.data?.error || err.message
          }`
        );
      } finally {
        setLoading(false);
      }
    };

    fetchModel();
  }, [sessionId]);

  // Функція повноекранного режиму
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch((err) => {
        console.error(`Помилка переходу в повноекранний режим: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  };

  // Відстеження зміни повноекранного режиму
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  // Функція збільшення/зменшення масштабу
  const handleZoomChange = (event, newValue) => {
    setZoom(newValue);
  };

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 0.5, 10));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 0.5, 1));
  };

  const handleResetView = () => {
    setZoom(2);
    setAutoRotate(false);
  };

  // Завантаження моделі
  const handleDownloadModel = () => {
    if (model) {
      const downloadUrl = apiService.getDownloadFileUrl(
        sessionId,
        model.model_url.split("/").pop()
      );
      window.open(downloadUrl, "_blank");
    }
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 8, textAlign: "center" }}>
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h5">Завантаження 3D-моделі...</Typography>
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
          to={`/results/${sessionId}`}
          variant="contained"
          startIcon={<ArrowBackIcon />}
        >
          Повернутися до результатів
        </Button>
      </Container>
    );
  }

  if (!model) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="warning" sx={{ mb: 3 }}>
          <AlertTitle>Модель не знайдено</AlertTitle>
          Не вдалося знайти 3D-модель для цієї сесії.
        </Alert>
        <Button
          component={RouterLink}
          to={`/results/${sessionId}`}
          variant="contained"
          startIcon={<ArrowBackIcon />}
        >
          Повернутися до результатів
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Button
          component={RouterLink}
          to={`/results/${sessionId}`}
          startIcon={<ArrowBackIcon />}
          variant="outlined"
        >
          Назад до результатів
        </Button>
        <Typography variant="h5" component="h1">
          3D-Переглядач
        </Typography>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleDownloadModel}
        >
          Завантажити
        </Button>
      </Box>

      {/* 3D-переглядач */}
      <Paper
        elevation={3}
        sx={{
          height: "70vh",
          width: "100%",
          overflow: "hidden",
          mb: 2,
          position: "relative",
        }}
        ref={containerRef}
      >
        <Canvas>
          <PerspectiveCamera makeDefault position={[0, 0, 5]} zoom={zoom} />
          <OrbitControls
            autoRotate={autoRotate}
            autoRotateSpeed={1}
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
          />

          {showGrid && (
            <ThreeGrid args={[gridSize, gridSize]} infiniteGrid={true} />
          )}

          <ambientLight intensity={0.5} />
          <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} />
          <directionalLight position={[-10, -10, -5]} intensity={0.5} />

          <Suspense fallback={<Loader />}>
            <Model url={model.model_url} modelType={model.model_type} />
            <Environment preset="city" />
          </Suspense>
        </Canvas>

        {/* Елементи управління, накладені на Canvas */}
        <Box
          sx={{
            position: "absolute",
            bottom: 16,
            left: 16,
            right: 16,
            display: "flex",
            justifyContent: "center",
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 1,
              borderRadius: 2,
              backdropFilter: "blur(8px)",
              bgcolor: "rgba(255, 255, 255, 0.8)",
            }}
          >
            <Stack direction="row" spacing={2} alignItems="center">
              <Tooltip title="Зменшити">
                <IconButton onClick={handleZoomOut} size="small">
                  <ZoomOutIcon />
                </IconButton>
              </Tooltip>

              <Slider
                value={zoom}
                min={1}
                max={10}
                step={0.1}
                onChange={handleZoomChange}
                sx={{ width: 100 }}
              />

              <Tooltip title="Збільшити">
                <IconButton onClick={handleZoomIn} size="small">
                  <ZoomInIcon />
                </IconButton>
              </Tooltip>

              <Divider orientation="vertical" flexItem />

              <FormControlLabel
                control={
                  <Switch
                    checked={showGrid}
                    onChange={(e) => setShowGrid(e.target.checked)}
                    size="small"
                  />
                }
                label="Сітка"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={autoRotate}
                    onChange={(e) => setAutoRotate(e.target.checked)}
                    size="small"
                  />
                }
                label="Обертання"
              />

              <Divider orientation="vertical" flexItem />

              <Tooltip title="Скинути вигляд">
                <IconButton onClick={handleResetView} size="small">
                  <RefreshIcon />
                </IconButton>
              </Tooltip>

              <Tooltip
                title={
                  isFullscreen
                    ? "Вийти з повноекранного режиму"
                    : "Повноекранний режим"
                }
              >
                <IconButton onClick={toggleFullscreen} size="small">
                  {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                </IconButton>
              </Tooltip>
            </Stack>
          </Paper>
        </Box>
      </Paper>

      {/* Інформація про модель */}
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Інформація про модель
        </Typography>

        <Typography variant="body1" paragraph>
          Тип моделі: <strong>{model.model_type.toUpperCase()}</strong>
        </Typography>

        <Typography variant="body2" color="text.secondary" paragraph>
          Ця 3D-модель була створена з набору 2D-зображень за допомогою методу
          Structure from Motion (SfM) та технології реконструкції поверхні. Ви
          можете обертати модель, масштабувати її та змінювати налаштування
          перегляду за допомогою елементів керування.
        </Typography>

        <Typography variant="body2">
          Для кращого результату завантажте модель і відкрийте її у
          спеціалізованому програмному забезпеченні для 3D-редагування, такому
          як Blender, MeshLab або інших програмах.
        </Typography>
      </Paper>
    </Container>
  );
};

export default ViewerPage;
