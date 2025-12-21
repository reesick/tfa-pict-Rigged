import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { AppKitButton, useAppKitAccount } from '@reown/appkit-react-native';
import axios from 'axios'; 
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = 'http://192.168.1.XX:8000/api/wallet/connect'; 

export const WalletConnectBtn = ({ onSyncSuccess }) => {
  const { address, isConnected } = useAppKitAccount();

  useEffect(() => {
    const syncWalletToBackend = async () => {
      if (isConnected && address) {
        try {
          const token = await AsyncStorage.getItem('access_token');
          
          if (!token) {
             console.log("No auth token found, cannot sync wallet to backend.");
             return;
          }

          const response = await axios.post(
            API_URL, 
            { wallet_address: address },
            {
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` 
              }
            }
          );
          
          console.log('Wallet Synced:', response.data);
          if (onSyncSuccess) onSyncSuccess(response.data);
          
        } catch (error) {
          console.error('Wallet Sync Failed:', error.response?.data || error.message);
        }
      }
    };

    syncWalletToBackend();
  }, [isConnected, address]);

  return (
    <View style={styles.container}>
      <AppKitButton 
        balance="show" 
        connectButtonLabel="Connect Wallet"
      />
      {isConnected && (
        <Text style={styles.statusText}>
          Synced: {address.slice(0, 6)}...{address.slice(-4)}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    marginVertical: 10,
  },
  statusText: {
    fontSize: 12,
    color: '#4CAF50', 
    marginTop: 5,
  }
});

export default WalletConnectBtn;