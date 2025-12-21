import { createAppKit } from '@reown/appkit-react-native';
import { EthersAdapter } from '@reown/appkit-adapter-ethers';
import { mainnet, polygon, arbitrum } from '@reown/appkit/networks';

export const projectId = '9d1b9220fa386497ca1387d6c4493b58';


const metadata = {
  name: 'AI Finance Assistant',
  description: 'AI-powered financial tracking and DeFi portfolio manager',
  url: 'our website url', // This domain must verify against your deep link in production
  icons: ['https://www.creativefabrica.com/wp-content/uploads/2018/11/Money-finance-logo-by-DEEMKA-STUDIO.jpg'], 
  redirect: {
    native: 'financeapp://', // MUST match the scheme in your app.json / Info.plist
    universal: 'https://financeapp.com/connect' // Optional: for Universal Links
  }
};


const ethersAdapter = new EthersAdapter();


export const appKit = createAppKit({
  projectId,
  metadata,
  networks: [mainnet, polygon, arbitrum], 
  adapters: [ethersAdapter],
  features: {
    analytics: true, 
    email: false,    
    socials: [],     
  },
  themeMode: 'light',
});