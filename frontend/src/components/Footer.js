import React from 'react';
import { Box, Container, Typography, Link, Grid } from '@mui/material';
import { GitHub, LinkedIn } from '@mui/icons-material';

const Footer = () => {
  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: 'auto',
        backgroundColor: (theme) => theme.palette.grey[900],
        color: 'white',
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <Typography variant="h6" gutterBottom>
              3D-Реконструкція з 2D-зображень
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
              Проект із відкритим вихідним кодом для перетворення звичайних фотографій в 3D-моделі.
              Використовує технології комп'ютерного зору та машинного навчання для реконструкції тривимірних об'єктів.
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} sx={{ display: 'flex', flexDirection: 'column', alignItems: { xs: 'flex-start', sm: 'flex-end' } }}>
            <Typography variant="h6" gutterBottom>
              Посилання
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Link href="https://github.com" target="_blank" rel="noopener" color="inherit">
                <GitHub />
              </Link>
              <Link href="https://linkedin.com" target="_blank" rel="noopener" color="inherit">
                <LinkedIn />
              </Link>
            </Box>
            <Typography variant="body2" sx={{ mt: 2, color: 'rgba(255, 255, 255, 0.7)' }}>
              © {new Date().getFullYear()} 3D-Реконструкція. Всі права захищено.
            </Typography>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default Footer;