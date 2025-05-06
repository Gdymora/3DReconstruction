import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Typography,
  Paper,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Chip
} from '@mui/material';
import {
  Lightbulb as LightbulbIcon,
  Camera as CameraIcon,
  Code as CodeIcon,
  ViewInAr as ViewIcon,
  Computer as ComputerIcon,
  CloudUpload as UploadIcon
} from '@mui/icons-material';

const technologies = [
  { name: 'Python', type: 'backend' },
  { name: 'Flask', type: 'backend' },
  { name: 'OpenCV', type: 'cv' },
  { name: 'COLMAP', type: 'cv' },
  { name: 'OpenMVS', type: 'cv' },
  { name: 'React', type: 'frontend' },
  { name: 'Three.js', type: 'frontend' },
  { name: 'Docker', type: 'devops' },
  { name: 'Nginx', type: 'devops' },
  { name: 'Open3D', type: 'cv' },
  { name: 'PyTorch', type: 'ml' },
  { name: 'WebGL', type: 'frontend' }
];

const AboutPage = () => {
  return (
    <Container maxWidth="lg">
      <Typography 
        variant="h4" 
        component="h1" 
        gutterBottom 
        sx={{ mb: 4, textAlign: 'center', fontWeight: 'bold' }}
      >
        Про проект
      </Typography>

      {/* Загальна інформація */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Що таке 3D-реконструкція з 2D-зображень?
        </Typography>
        
        <Typography variant="body1" paragraph>
          3D-реконструкція з 2D-зображень — це процес створення тривимірних моделей об'єктів на основі 
          набору звичайних фотографій. Ця технологія використовує алгоритми комп'ютерного зору та 
          машинного навчання для аналізу зображень, виявлення спільних точок між ними та обчислення 
          просторового розташування об'єктів.
        </Typography>
        
        <Typography variant="body1" paragraph>
          Наш проект надає веб-інтерфейс, який дозволяє користувачам створювати власні 3D-моделі, 
          використовуючи простий і зрозумілий процес: завантаження зображень, налаштування параметрів, 
          запуск реконструкції та отримання результатів.
        </Typography>
      </Paper>

      {/* Як це працює */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Як це працює
        </Typography>
        
        <Grid container spacing={3} sx={{ mb: 2 }}>
          <Grid item xs={12} md={6}>
            <List>
              <ListItem alignItems="flex-start">
                <ListItemIcon>
                  <CameraIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="1. Завантаження зображень"
                  secondary="Користувач завантажує серію фотографій об'єкта, зроблених з різних ракурсів. Для найкращого результату рекомендується 10-30 зображень з хорошим перекриттям між ними."
                />
              </ListItem>
              
              <ListItem alignItems="flex-start">
                <ListItemIcon>
                  <LightbulbIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="2. Аналіз особливостей"
                  secondary="Система виявляє ключові точки на зображеннях та встановлює відповідності між ними. Це дозволяє визначити, які частини зображень відповідають одним і тим же точкам об'єкта в реальному світі."
                />
              </ListItem>
              
              <ListItem alignItems="flex-start">
                <ListItemIcon>
                  <ComputerIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="3. Structure from Motion (SfM)"
                  secondary="Алгоритм SfM обчислює позиції камери для кожного зображення та створює розріджену хмару точок, яка представляє базову структуру об'єкта в 3D-просторі."
                />
              </ListItem>
            </List>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <List>
              <ListItem alignItems="flex-start">
                <ListItemIcon>
                  <CodeIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="4. Щільна реконструкція"
                  secondary="Система генерує щільну хмару точок з набагато вищою деталізацією, використовуючи алгоритми Multi-View Stereo (MVS)."
                />
              </ListItem>
              
              <ListItem alignItems="flex-start">
                <ListItemIcon>
                  <ViewIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="5. Створення мешу"
                  secondary="З хмари точок створюється полігональна поверхня (меш), що представляє об'єкт. Цей процес включає фільтрацію шуму, згладжування та оптимізацію геометрії."
                />
              </ListItem>
              
              <ListItem alignItems="flex-start">
                <ListItemIcon>
                  <UploadIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="6. Експорт результатів"
                  secondary="Готова 3D-модель експортується в різних форматах (OBJ, PLY, GLTF) для перегляду в браузері або використання у зовнішніх програмах."
                />
              </ListItem>
            </List>
          </Grid>
        </Grid>
      </Paper>

      {/* Використані технології */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Використані технології
        </Typography>
        
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Основний стек
          </Typography>
          
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mb: 2 }}>
            {technologies.map((tech, index) => (
              <Chip 
                key={index} 
                label={tech.name} 
                color={
                  tech.type === 'backend' ? 'primary' :
                  tech.type === 'frontend' ? 'secondary' :
                  tech.type === 'cv' ? 'success' :
                  tech.type === 'ml' ? 'info' :
                  'default'
                }
                sx={{ m: 0.5 }}
              />
            ))}
          </Stack>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            Схема системи
          </Typography>
          
          <Box sx={{ textAlign: 'center' }}>
            <Box
              component="img"
              src="/system-diagram.jpg"
              alt="Схема системи 3D-реконструкції"
              sx={{
                maxWidth: '100%',
                height: 'auto',
                borderRadius: 1,
                mb: 2
              }}
            />
            <Typography variant="caption" color="text.secondary">
              Спрощена архітектура системи 3D-реконструкції
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Обмеження та плани розвитку */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Обмеження та плани розвитку
        </Typography>
        
        <Typography variant="body1" paragraph>
          <strong>Поточні обмеження:</strong>
        </Typography>
        
        <List dense>
          <ListItem>
            <ListItemText primary="Система працює найкраще з об'єктами, що мають чітку текстуру та не є прозорими або дзеркальними." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Максимальна кількість зображень обмежена для збереження прийнятного часу обробки." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Реконструкція великомасштабних сцен (наприклад, цілих будівель або територій) може бути менш точною без додаткової геопросторової інформації." />
          </ListItem>
        </List>
        
        <Typography variant="body1" paragraph sx={{ mt: 2 }}>
          <strong>Плани розвитку:</strong>
        </Typography>
        
        <List dense>
          <ListItem>
            <ListItemText primary="Інтеграція з мобільними додатками для безпосереднього захоплення зображень." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Покращення алгоритмів текстурування для більш реалістичних результатів." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Реалізація семантичної сегментації для автоматичного розпізнавання та розділення об'єктів у сцені." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Створення API для інтеграції з іншими системами та додатками." />
          </ListItem>
        </List>
      </Paper>

      {/* Контакти та посилання */}
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Контакти та посилання
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Репозиторій проекту
            </Typography>
            <Typography variant="body1" paragraph>
              Проект доступний на GitHub з відкритим вихідним кодом під ліцензією MIT.
            </Typography>
            <Button 
              variant="outlined" 
              startIcon={<CodeIcon />}
              href="https://github.com/username/3d-reconstruction"
              target="_blank"
              sx={{ mb: 2 }}
            >
              GitHub репозиторій
            </Button>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Спробувати зараз
            </Typography>
            <Typography variant="body1" paragraph>
              Готові створити власну 3D-модель? Переходьте до завантаження зображень!
            </Typography>
            <Button 
              variant="contained" 
              component={RouterLink}
              to="/upload"
              startIcon={<UploadIcon />}
            >
              Створити 3D-модель
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default AboutPage;