import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

const features = [
  {
    eyebrow: 'Question',
    title: 'Does tract resolution add information?',
    body: 'We compare direct tract measures with direct community-area labels for the same condition and period.',
    link: '/methods/scientific-question',
  },
  {
    eyebrow: 'Methods',
    title: 'Every estimand is explicit',
    body: 'Pooling, variance partitioning, rank gaps, quartiles, cluster bootstrap uncertainty, and spatial methods are documented.',
    link: '/methods/estimands',
  },
  {
    eyebrow: 'Boundary',
    title: 'Supplement, not replace',
    body: 'Health-system EHR data describe diagnoses among observed adults. Population surveillance remains the basis for population inference.',
    link: '/methods/limitations',
  },
];

function Home(): ReactNode {
  return (
    <Layout
      title="Chicago Health Map Methods"
      description="Methods and reproducibility for the Chicago Health Map geographic-resolution study">
      <main>
        <header className={styles.hero}>
          <div className="container">
            <div className={styles.kicker}>Chicago Health Map geographic-resolution study</div>
            <Heading as="h1" className={styles.heroTitle}>
              How we tested whether tract-level health-system data add geographic information
            </Heading>
            <p className={styles.heroSubtitle}>
              A transparent account of the data, denominators, statistical estimands, uncertainty methods,
              results, and interpretation boundaries behind the final aggregate analysis.
            </p>
            <div className={styles.actions}>
              <Link className="button button--primary button--lg" to="/methods/">
                Read the methods
              </Link>
              <Link className="button button--outline button--secondary button--lg" to="/methods/results-guide">
                See the results guide
              </Link>
            </div>
          </div>
        </header>

        <section className={styles.statement}>
          <div className="container">
            <p>
              Chicago Health Map describes EHR-diagnosed proportions among adults observed in participating
              CAPriCORN health systems. The study evaluates whether those data can complement public-health
              surveillance at smaller geographic scales. It does not treat them as population prevalence.
            </p>
          </div>
        </section>

        <section className={styles.features}>
          <div className="container">
            <div className="row">
              {features.map((feature) => (
                <div className={clsx('col col--4', styles.featureColumn)} key={feature.title}>
                  <article className={styles.card}>
                    <div className={styles.eyebrow}>{feature.eyebrow}</div>
                    <Heading as="h2">{feature.title}</Heading>
                    <p>{feature.body}</p>
                    <Link to={feature.link}>Explore this section →</Link>
                  </article>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.resultBand}>
          <div className="container">
            <div className={styles.resultGrid}>
              <div>
                <span className={styles.metric}>35.3%</span>
                <span className={styles.metricLabel}>hypertension tract quartiles disagreed with community-area labels</span>
              </div>
              <div>
                <span className={styles.metric}>50.1%</span>
                <span className={styles.metricLabel}>COPD tract quartiles disagreed with community-area labels</span>
              </div>
              <div>
                <span className={styles.metric}>782</span>
                <span className={styles.metricLabel}>tracts in the primary Chicago boundary frame</span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}

export default Home;
