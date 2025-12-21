import '@walletconnect/react-native-compat';
import 'react-native-get-random-values';

import './src/config/web3Config.js'; 

import { AppRegistry } from 'react-native';
import App from './App';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);