import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Grid,
  Typography,
  Card,
  CardContent,
  CardMedia,
  CardActionArea,
  Stack
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Speed as SpeedIcon,
  SettingsApplications as SettingsIcon,
  ViewInAr as ViewIcon
} from '@mui/icons-material';

const features = [
  {
    icon: <SpeedIcon sx={{ fontSize: 60 }} color="primary" />,
    title: 'Швидка реконструкція',
    description: 'Наша система забезпечує швидке перетворення звичайних фотографій в 3D-моделі використовуючи оптимізовані алгоритми комп\'ютерного зору.'
  },
  {
    icon: <SettingsIcon sx={{ fontSize: 60 }} color="primary" />,
    title: 'Гнучкі налаштування',
    description: 'Виберіть пріоритет між якістю та швидкістю обробки. Налаштуйте параметри реконструкції під ваші потреби.'
  },
  {
    icon: <ViewIcon sx={{ fontSize: 60 }} color="primary" />,
    title: 'Інтерактивний перегляд',
    description: 'Вбудований 3D-переглядач дозволяє інтерактивно досліджувати згенеровані моделі прямо у браузері без додаткового програмного забезпечення.'
  }
];

const HomePage = () => {
  return (
    <Container>
      {/* Основний Hero-блок */}
      <Box
        sx={{
          py: 8,
          textAlign: 'center',
          borderRadius: 2,
          mb: 6
        }}
      >
        <Typography 
          variant="h2" 
          component="h1" 
          gutterBottom 
          sx={{ fontWeight: 'bold', mb: 3 }}
        >
          Перетворіть фото в 3D-модель
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph sx={{ maxWidth: 800, mx: 'auto', mb: 4 }}>
          Інноваційна система на основі штучного інтелекту та комп'ютерного зору для створення тривимірних
          моделей з набору звичайних фотографій.
        </Typography>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          justifyContent="center"
          sx={{ mb: 5 }}
        >
          <Button 
            variant="contained" 
            size="large" 
            component={RouterLink}
            to="/upload"
            endIcon={<UploadIcon />}
          >
            Створити 3D-модель
          </Button>
          <Button 
            variant="outlined" 
            size="large"
            component={RouterLink}
            to="/about"
          >
            Дізнатися більше
          </Button>
        </Stack>
        <Box
          component="img"
          src="/placeholder-hero.jpg"
          alt="3D реконструкція прикладу"
          sx={{
            width: '100%',
            maxWidth: 800,
            height: 'auto',
            borderRadius: 2,
            boxShadow: 3,
            mx: 'auto'
          }}
        />
      </Box>

      {/* Блок функцій */}
      <Typography 
        variant="h4" 
        component="h2" 
        sx={{ mb: 4, textAlign: 'center', fontWeight: 'bold' }}
      >
        Ключові можливості
      </Typography>
      <Grid container spacing={4} sx={{ mb: 8 }}>
        {features.map((feature, index) => (
          <Grid item key={index} xs={12} md={4}>
            <Box sx={{ textAlign: 'center', height: '100%' }}>
              <Box sx={{ mb: 2 }}>
                {feature.icon}
              </Box>
              <Typography variant="h5" component="h3" gutterBottom>
                {feature.title}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {feature.description}
              </Typography>
            </Box>
          </Grid>
        ))}
      </Grid>

      {/* Блок прикладів */}
      <Typography 
        variant="h4" 
        component="h2" 
        sx={{ mb: 4, textAlign: 'center', fontWeight: 'bold' }}
      >
        Приклади реконструкцій
      </Typography>
      <Grid container spacing={3} sx={{ mb: 8 }}>
        {[1, 2, 3].map((item) => (
          <Grid item key={item} xs={12} sm={6} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardActionArea>
                <CardMedia
                  component="img"
                  height="200"
                  image={`/placeholder-example-${item}.jpg`}
                  alt={`Приклад 3D реконструкції ${item}`}
                />
                <CardContent>
                  <Typography gutterBottom variant="h6" component="div">
                    Приклад реконструкції {item}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Модель створена з {5 + item} зображень. Використовувався метод колаборативної реконструкції з глибинним навчанням.
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Заклик до дії */}
      <Box
        sx={{
          bgcolor: 'primary.light',
          py: 6,
          px: 4,
          borderRadius: 2,
          textAlign: 'center',
          mb: 6
        }}
      >
        <Typography variant="h4" component="h2" color="white" gutterBottom>
          Готові спробувати?
        </Typography>
        <Typography variant="body1" color="white" paragraph>
          Завантажте декілька фотографій об'єкта з різних ракурсів і отримайте 3D-модель вже за кілька хвилин!
        </Typography>
        <Button 
          variant="contained" 
          size="large" 
          component={RouterLink}
          to="/upload"
          color="secondary"
          endIcon={<UploadIcon />}
          sx={{ mt: 2 }}
        >
          Почати зараз
        </Button>
      </Box>
    </Container>
  );
};

export default HomePage;