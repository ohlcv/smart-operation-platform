import { defineConfig, loadEnv } from 'vite'
import path from 'path'
import createVitePlugins from './vite/plugins'

// https://vitejs.dev/config/
export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd())
  const { VITE_APP_ENV } = env
  return {
    // 部署生产环境和开发环境下的URL。
    // 默认情况下，vite 会假设你的应用是被部署在一个域名的根路径上
    // 例如 https://www.ruoyi.vip/。如果应用被部署在一个子路径上，你就需要用这个选项指定这个子路径。例如，如果你的应用被部署在 https://www.ruoyi.vip/admin/，则设置 baseUrl 为 /admin/。
    base: VITE_APP_ENV === 'production' ? '/' : '/',
    plugins: createVitePlugins(env, command === 'build'),
    resolve: {
      // https://cn.vitejs.dev/config/#resolve-alias
      alias: {
        // 设置路径
        '~': path.resolve(__dirname, './'),
        // 设置别名
        '@': path.resolve(__dirname, './src')
      },
      // https://cn.vitejs.dev/config/#resolve-extensions
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    // 打包配置
    build: {
      // https://vite.dev/config/build-options.html
      sourcemap: command === 'build' ? false : 'inline',
      outDir: 'dist',
      assetsDir: 'assets',
      chunkSizeWarningLimit: 2000,
      rollupOptions: {
        output: {
          chunkFileNames: 'static/js/[name]-[hash].js',
          entryFileNames: 'static/js/[name]-[hash].js',
          assetFileNames: 'static/[ext]/[name]-[hash].[ext]'
        }
      }
    },
    // vite 相关配置
    server: {
      port: 80,
      host: true,
      open: true,
      proxy: {
        // https://cn.vitejs.dev/config/#server-proxy
        // 反向代理后端 RESTful API
        '/dev-api': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/dev-api/, '')
        },
        // 反向代理后端 API 文档相关路径（vite.config.js 详解见
        // docs/04-开发/DEBUG/swagger-ui-relative-openapi-yaml-exception-2026-07-11.md）
        //
        // 为什么需要单独代理这些路径：
        //   swagger UI / redoc HTML 内部声明 openapiUrl='/openapi.json'（相对路径），
        //   iframe src='/dev-api/proxy-docs' 内浏览器解析该相对 URL 时，根 host 仍是
        //   前端 dev server，无法被 '/dev-api' 模式匹配 → 走 SPA fallback 拿到
        //   index.html，被 swagger-ui 当 openapi JSON 解析 → YAMLException。
        //   故把后端 docs 路由直接挂在 '/dev-api' 之外，由 Vite 原样转发（rewrite 保持原路径）：
        '/proxy-docs': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true
        },
        '/proxy-openapi.json': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true
        },
        '/proxy-redoc': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true
        },
        // swagger/redoc HTML 内部使用相对路径 '/openapi.json' 加载 schema，
        // iframe 内浏览器把它解析为前端 host 的根路径 '/openapi.json'，
        // 因此需要把 '/openapi.json' 也代理到后端，否则会走 SPA fallback 返回 index.html。
        '/openapi.json': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true
        }
      }
    },
    //fix:error:stdin>:7356:1: warning: "@charset" must be the first rule in the file
    css: {
      postcss: {
        plugins: [
          {
            postcssPlugin: 'internal:charset-removal',
            AtRule: {
              charset: (atRule) => {
                if (atRule.name === 'charset') {
                  atRule.remove();
                }
              }
            }
          }
        ]
      }
    }
  }
})
