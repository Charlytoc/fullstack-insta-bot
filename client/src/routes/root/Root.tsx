import { Navbar } from "../../components/Navbar/Navbar";
import "./rootStyles.css";
import { useTranslation } from 'react-i18next';

const REDIRECT_URI = "https://fullstack-insta-bot.onrender.com//authorize/"
export default function Root() {
  const { t } = useTranslation();

  return (
    <>
      <Navbar />
      <header className="hero-section">
        <h1>{t('heroTitle')}</h1>
        <p>{t('heroDescription')}</p>
      </header>
      <main>
        <h3>{t('mainTitle')}</h3>
        <section>
          <h2>{t('step1Title')}</h2>
          <p>{t('step1Description')}</p>
          <a href={`https://www.instagram.com/oauth/authorize?client_id=464050633149224&redirect_uri=${REDIRECT_URI}&response_type=code&scope=business_basic%2Cbusiness_manage_messages%2Cbusiness_manage_comments%2Cbusiness_content_publish`}>Authorize</a>
        </section>
        <section>
          <h2>{t('step2Title')}</h2>
          <p>{t('step2Description')}</p>
        </section>
        <section>
          <h2>{t('step3Title')}</h2>
          <p>{t('step3Description')}</p>
        </section>
      </main>
      <footer>
        <p>&copy; 2023 {t('footerText')}</p>
      </footer>
    </>
  );
}
