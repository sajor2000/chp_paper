import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import rehypeKatex from 'rehype-katex';
import remarkMath from 'remark-math';

const config: Config = {
  title: 'Chicago Health Map Methods',
  tagline: 'How health-system data can supplement public-health surveillance at smaller geographic scales',
  favicon: 'img/chm-mark.svg',

  future: {
    v4: true,
  },

  url: 'https://sajor2000.github.io',
  baseUrl: '/chp_paper/',
  organizationName: 'sajor2000',
  projectName: 'chp_paper',
  trailingSlash: false,
  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: 'methods',
          sidebarPath: './sidebars.ts',
          editUrl: ({docPath}) =>
            `https://github.com/sajor2000/chp_paper/edit/main/website/docs/${docPath}`,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
          showLastUpdateTime: true,
          showLastUpdateAuthor: false,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/chm-social-card.svg',
    metadata: [
      {
        name: 'description',
        content:
          'Methods, statistical estimands, results, and reproducibility documentation for the Chicago Health Map geographic-resolution study.',
      },
    ],
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'CHM Methods',
      logo: {
        alt: 'Chicago Health Map methods mark',
        src: 'img/chm-mark.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'methodsSidebar',
          position: 'left',
          label: 'Methods',
        },
        {
          to: '/methods/results-guide',
          label: 'Results guide',
          position: 'left',
        },
        {
          href: 'https://github.com/sajor2000/chp_paper',
          label: 'Code and artifacts',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Study',
          items: [
            {label: 'Scientific question', to: '/methods/scientific-question'},
            {label: 'Statistical methods', to: '/methods/statistical-methods'},
            {label: 'Limitations', to: '/methods/limitations'},
          ],
        },
        {
          title: 'Reproducibility',
          items: [
            {label: 'Reproduce the analysis', to: '/methods/reproducibility'},
            {
              label: 'GitHub repository',
              href: 'https://github.com/sajor2000/chp_paper',
            },
          ],
        },
        {
          title: 'Data context',
          items: [
            {label: 'Chicago Health Map', href: 'https://chicagohealthmap.com'},
            {
              label: 'Chicago Health Map glossary',
              href: 'https://chicagohealthmap.com/data-glossary',
            },
          ],
        },
      ],
      copyright: `Chicago Health Map study methods, ${new Date().getFullYear()}. Built with Docusaurus.`,
    },
    docs: {
      sidebar: {
        hideable: true,
        autoCollapseCategories: true,
      },
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css',
      type: 'text/css',
      integrity:
        'sha384-5TcZemv2l/9On385z///+d7MSYlvIEw9FuZTIdZ14vJLqWphw7e7ZPuOiCHJcFCP',
      crossorigin: 'anonymous',
    },
  ],
};

export default config;
