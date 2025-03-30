import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    adapter: adapter({
      // Output directory for the static build
      fallback: 'index.html'
    })
  }
};

export default config;