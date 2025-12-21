import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import WalletConnectBtn from '../components/WalletConnectBtn';

const PortfolioScreen = () => {
  
  const handleWalletSync = (data) => {
    console.log("New wallet added, refreshing charts...", data);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>DeFi Portfolio</Text>
      
      <WalletConnectBtn onSyncSuccess={handleWalletSync} />
      
      <View style={styles.placeholder}>
        <Text>Connect wallet to see assets...</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, paddingTop: 50 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  placeholder: { flex: 1, justifyContent: 'center', alignItems: 'center' }
});

export default PortfolioScreen;