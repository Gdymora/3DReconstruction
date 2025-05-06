import React, { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  RadioGroup,
  FormControlLabel,
  Radio,
  Paper,
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  AlertTitle,
} from "@mui/material";
import {
  CloudUpload as UploadIcon,
  DeleteForever as DeleteIcon,
  Check as CheckIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import { useDropzone } from "react-dropzone";
import { toast } from "react-toastify";
import apiService from "../services/apiService";

const UploadPage = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [quality, setQuality] = useState("medium");
  const [method, setMethod] = useState("colmap");
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [result, setResult] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const imageFiles = acceptedFiles.filter((file) =>
      file.type.startsWith("image/")
    );

    if (imageFiles.length !== acceptedFiles.length) {
      toast.warning(
        "Деякі файли було відхилено. Підтримуються лише формати зображень."
      );
    }

    const filesWithPreview = imageFiles.map((file) =>
      Object.assign(file, {
        preview: URL.createObjectURL(file),
      })
    );

    setFiles((prev) => [...prev, ...filesWithPreview]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpeg", ".jpg", ".png", ".tiff", ".tif"],
    },
  });

  const removeFile = (fileToRemove) => {
    setFiles(files.filter((file) => file !== fileToRemove));
    URL.revokeObjectURL(fileToRemove.preview);
  };

  const clearFiles = () => {
    files.forEach((file) => URL.revokeObjectURL(file.preview));
    setFiles([]);
  };

  const handleUpload = async () => {
    if (files.length < 3) {
      toast.error(
        "Необхідно завантажити щонайменше 3 зображення для 3D-реконструкції."
      );
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const response = await apiService.uploadImages(files, (progressEvent) => {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setUploadProgress(progress);
      });

      if (response.status === 200 && response.data.session_id) {
        toast.success("Зображення успішно завантажено!");
        setSessionId(response.data.session_id);
        setIsUploading(false);
      } else {
        throw new Error("Неочікувана відповідь сервера");
      }
    } catch (error) {
      setIsUploading(false);
      console.error("Помилка завантаження:", error);
      toast.error(
        `Помилка завантаження: ${error.response?.data?.error || error.message}`
      );
    }
  };

  const startReconstruction = async () => {
    setIsProcessing(true);
    setStatusMessage("Запуск реконструкції...");

    try {
      // Запуск реконструкції
      const response = await apiService.reconstructModel(
        sessionId,
        quality,
        method
      );

      // Перевірка статусу
      if (
        response.data.status === "processing" ||
        response.data.status === "uploaded"
      ) {
        // Перенаправляємо на сторінку з результатами відразу
        navigate(`/results/${sessionId}`);
      } else if (response.data.status === "completed") {
        // Одразу отримали результат
        setResult(response.data);
        setIsProcessing(false);
        setStatusMessage("Реконструкція завершена!");

        toast.success("3D-модель успішно створена!");

        // Перенаправляємо на сторінку з результатами
        navigate(`/results/${sessionId}`);
      }
    } catch (error) {
      console.error("Помилка реконструкції:", error);
      setIsProcessing(false);
      setStatusMessage(
        `Помилка: ${
          error.response?.data?.error || error.message || "Невідома помилка"
        }`
      );
      toast.error(
        `Помилка реконструкції: ${
          error.response?.data?.error || error.message || "Невідома помилка"
        }`
      );
    }
  };

  // Функція для перевірки статусу Можна видалити оскільки одразу перенаправляємо на сторінку з результатами
  const checkStatus = async (sessionId) => {
    try {
      const response = await apiService.getReconstructionStatus(sessionId);
      const status = response.data.status;

      // Оновлюємо повідомлення про статус
      if (status === "processing") {
        // Якщо є інформація про прогрес, оновлюємо її
        const elapsed = response.data.elapsed_time || 0;
        setStatusMessage(
          `Реконструкція в процесі... Минуло: ${Math.floor(elapsed / 60)}m ${
            elapsed % 60
          }s`
        );

        // Перевіряємо статус знову через 5 секунд
        setTimeout(() => checkStatus(sessionId), 5000);
      } else if (status === "completed") {
        // Реконструкція завершена
        setResult(response.data);
        setIsProcessing(false);
        setStatusMessage("Реконструкція успішно завершена!");

        toast.success("3D-модель успішно створена!");

        // Перенаправляємо на сторінку з результатами
        if (response.data.model_url) {
          navigate(`/results/${sessionId}`);
        }
      } else if (status === "failed") {
        // Помилка реконструкції
        setIsProcessing(false);
        setStatusMessage(
          `Помилка реконструкції: ${response.data.error || "Невідома помилка"}`
        );
        toast.error(
          `Помилка реконструкції: ${response.data.error || "Невідома помилка"}`
        );
      }
    } catch (error) {
      console.error("Помилка при перевірці статусу:", error);
      setStatusMessage(`Помилка при перевірці статусу: ${error.message}`);
      // Продовжуємо перевіряти, можливо це тимчасова проблема
      setTimeout(() => checkStatus(sessionId), 10000);
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography
        variant="h4"
        component="h1"
        gutterBottom
        sx={{ mb: 4, textAlign: "center", fontWeight: "bold" }}
      >
        Створення 3D-моделі
      </Typography>

      <Grid container spacing={4}>
        {/* Ліва колонка для завантаження */}
        <Grid item xs={12} md={7}>
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Крок 1: Завантажте зображення
            </Typography>

            <Alert severity="info" sx={{ mb: 2 }}>
              <AlertTitle>Поради для кращих результатів</AlertTitle>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    <CheckIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Зробіть 10-20 фотографій об'єкта з різних ракурсів" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    <CheckIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Забезпечте рівномірне освітлення без відблисків" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    <CheckIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Уникайте прозорих або дуже блискучих об'єктів" />
                </ListItem>
              </List>
            </Alert>

            <Box
              {...getRootProps()}
              sx={{
                border: "2px dashed",
                borderColor: isDragActive ? "primary.main" : "grey.400",
                borderRadius: 2,
                p: 3,
                textAlign: "center",
                bgcolor: isDragActive
                  ? "rgba(25, 118, 210, 0.1)"
                  : "background.paper",
                cursor: "pointer",
                transition: "all 0.2s ease",
                mb: 3,
              }}
            >
              <input {...getInputProps()} />
              <UploadIcon sx={{ fontSize: 40, mb: 1, color: "primary.main" }} />
              <Typography variant="h6" component="p">
                {isDragActive
                  ? "Відпустіть файли тут..."
                  : "Перетягніть зображення сюди або клацніть для вибору"}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Підтримуються формати JPG, PNG, TIFF
              </Typography>
            </Box>

            {isUploading && (
              <Box sx={{ mb: 3, textAlign: "center" }}>
                <CircularProgress
                  variant="determinate"
                  value={uploadProgress}
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" color="text.secondary">
                  Завантаження: {uploadProgress}%
                </Typography>
              </Box>
            )}

            {files.length > 0 && (
              <Box>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    mb: 2,
                  }}
                >
                  <Typography variant="subtitle1">
                    Завантажені зображення ({files.length})
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={clearFiles}
                    disabled={isUploading}
                  >
                    Очистити все
                  </Button>
                </Box>

                <Grid container spacing={2}>
                  {files.map((file, index) => (
                    <Grid item xs={6} sm={4} md={3} key={index}>
                      <Card sx={{ position: "relative" }}>
                        <Box
                          component="img"
                          src={file.preview}
                          alt={`Preview ${index + 1}`}
                          sx={{
                            height: 120,
                            width: "100%",
                            objectFit: "cover",
                            display: "block",
                          }}
                        />
                        <Button
                          variant="contained"
                          color="error"
                          size="small"
                          sx={{
                            position: "absolute",
                            top: 5,
                            right: 5,
                            minWidth: "auto",
                            width: 24,
                            height: 24,
                            p: 0,
                          }}
                          onClick={() => removeFile(file)}
                          disabled={isUploading}
                        >
                          <DeleteIcon fontSize="small" />
                        </Button>
                        <CardContent sx={{ py: 1, px: 1 }}>
                          <Typography variant="caption" noWrap>
                            {file.name}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>

                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<UploadIcon />}
                  sx={{ mt: 3 }}
                  onClick={handleUpload}
                  disabled={
                    isUploading || files.length === 0 || sessionId !== null
                  }
                >
                  {isUploading ? "Завантаження..." : "Завантажити зображення"}
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Права колонка для налаштувань та реконструкції */}
        <Grid item xs={12} md={5}>
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Крок 2: Налаштування реконструкції
            </Typography>

            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel id="quality-label">Якість реконструкції</InputLabel>
              <Select
                labelId="quality-label"
                id="quality-select"
                value={quality}
                label="Якість реконструкції"
                onChange={(e) => setQuality(e.target.value)}
                disabled={!sessionId || isProcessing}
              >
                <MenuItem value="low">Низька (швидше)</MenuItem>
                <MenuItem value="medium">Середня (рекомендовано)</MenuItem>
                <MenuItem value="high">Висока (повільніше)</MenuItem>
              </Select>
            </FormControl>

            <Typography variant="subtitle1" gutterBottom>
              Метод реконструкції
            </Typography>
            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <RadioGroup
                value={method}
                onChange={(e) => setMethod(e.target.value)}
              >
                <FormControlLabel
                  value="colmap"
                  control={<Radio />}
                  label="COLMAP (класичний метод)"
                  disabled={!sessionId || isProcessing}
                />
                <FormControlLabel
                  value="openmvs"
                  control={<Radio />}
                  label="OpenMVS (висока деталізація)"
                  disabled={!sessionId || isProcessing}
                />
                <FormControlLabel
                  value="custom"
                  control={<Radio />}
                  label="Нейронна мережа (експериментальний)"
                  disabled={!sessionId || isProcessing}
                />
              </RadioGroup>
            </FormControl>
            {statusMessage && (
              <Alert
                severity={
                  statusMessage.includes("Помилка")
                    ? "error"
                    : statusMessage.includes("завершена")
                    ? "success"
                    : "info"
                }
                sx={{ mb: 2 }}
              >
                {statusMessage}
              </Alert>
            )}
            <Box sx={{ textAlign: "center" }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={startReconstruction}
                disabled={!sessionId || isProcessing}
                fullWidth
                sx={{ mb: 2 }}
              >
                {isProcessing ? (
                  <>
                    <CircularProgress
                      size={24}
                      sx={{ mr: 1, color: "white" }}
                    />
                    Обробка...
                  </>
                ) : (
                  "Створити 3D-модель"
                )}
              </Button>

              {!sessionId && (
                <Typography variant="body2" color="text.secondary">
                  Спочатку завантажте зображення в кроці 1
                </Typography>
              )}
            </Box>
          </Paper>

          <Paper elevation={3} sx={{ p: 3 }}>
            <Box sx={{ display: "flex", alignItems: "flex-start", mb: 2 }}>
              <InfoIcon color="info" sx={{ mr: 1, mt: 0.5 }} />
              <Typography variant="h6">Про процес</Typography>
            </Box>
            <Typography variant="body2" paragraph>
              Після завантаження зображень система проаналізує їх для виявлення
              спільних точок і визначення позицій камери. На основі цієї
              інформації буде створена 3D-модель об'єкта.
            </Typography>
            <Typography variant="body2" paragraph>
              Час обробки залежить від кількості зображень, їх роздільної
              здатності та обраної якості. Зазвичай процес займає від 1 до 10
              хвилин.
            </Typography>
            <Typography variant="body2">
              Готову модель можна буде завантажити в форматах OBJ, GLTF або
              переглянути безпосередньо в браузері.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default UploadPage;
