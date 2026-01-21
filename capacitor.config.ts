import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
    appId: 'com.tradewise.app',
    appName: 'TradeWise',
    webDir: 'static',
    server: {
        androidScheme: 'https',
        // For development, uncomment to use live reload:
        // url: 'http://YOUR_LOCAL_IP:8000',
        // cleartext: true
    },
    plugins: {
        SplashScreen: {
            launchAutoHide: true,
            launchShowDuration: 2000,
            backgroundColor: '#0a0a0f',
            showSpinner: true,
            spinnerColor: '#3b82f6'
        },
        StatusBar: {
            style: 'DARK',
            backgroundColor: '#0a0a0f'
        }
    },
    android: {
        allowMixedContent: true,
        webContentsDebuggingEnabled: true
    }
};

export default config;
