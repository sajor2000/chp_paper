import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  methodsSidebar: [
    'overview',
    {
      type: 'category',
      label: 'Why and what we studied',
      collapsed: false,
      items: ['scientific-question', 'data-sources', 'analytic-cohort'],
    },
    {
      type: 'category',
      label: 'How we analyzed it',
      collapsed: false,
      items: ['estimands', 'statistical-methods'],
    },
    {
      type: 'category',
      label: 'What the analysis showed',
      collapsed: false,
      items: ['results-guide', 'limitations'],
    },
    'reproducibility',
  ],
};

export default sidebars;
