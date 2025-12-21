import React from 'react';
import { SafeAreaView, StatusBar, StyleSheet } from 'react-native';
import PortfolioScreen from './src/screens/PortfolioScreen.js'; 

const App = () => {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <PortfolioScreen />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
});

export default App;