// src/i18n.js
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enTranslation from './locales/en/translation.json';
import esTranslation from './locales/es/translation.json';

const browserLanguage = navigator.language || navigator.languages[0];

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        translation: enTranslation
      },
      es: {
        translation: esTranslation
      }
    },
    // lng: browserLanguage.startsWith('es') ? 'es' : 'en', 
    lng:  'es', 
    fallbackLng: 'es',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
