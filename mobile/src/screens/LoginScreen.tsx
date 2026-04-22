import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator, Alert,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useAuthStore } from '../store/authStore';
import { colors, spacing, radius, typography } from '../theme/colors';
import type { AuthStackParamList } from '../../App';

type Props = { navigation: NativeStackNavigationProp<AuthStackParamList, 'Login'> };

export default function LoginScreen({ navigation }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('Missing fields', 'Please enter your username and password.');
      return;
    }
    setLoading(true);
    try {
      await login(username.trim(), password);
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? 'Invalid credentials. Please try again.';
      Alert.alert('Login failed', detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.logo}>🌻</Text>
          <Text style={styles.title}>Sunflower Health</Text>
          <Text style={styles.subtitle}>Your personal wellness companion</Text>
        </View>

        {/* Form */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Welcome back</Text>

          <Text style={styles.label}>Username</Text>
          <TextInput
            style={styles.input}
            value={username}
            onChangeText={setUsername}
            placeholder="Enter your username"
            placeholderTextColor={colors.textMuted}
            autoCapitalize="none"
            autoCorrect={false}
          />

          <Text style={styles.label}>Password</Text>
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            placeholder="Enter your password"
            placeholderTextColor={colors.textMuted}
            secureTextEntry
          />

          <TouchableOpacity
            style={[styles.btn, loading && styles.btnDisabled]}
            onPress={handleLogin}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading
              ? <ActivityIndicator color={colors.textOnPrimary} />
              : <Text style={styles.btnText}>Sign In</Text>
            }
          </TouchableOpacity>
        </View>

        {/* Register link */}
        <TouchableOpacity onPress={() => navigation.navigate('Register')} style={styles.linkRow}>
          <Text style={styles.linkText}>New here? </Text>
          <Text style={[styles.linkText, styles.linkBold]}>Create an account →</Text>
        </TouchableOpacity>

        <Text style={styles.disclaimer}>
          Sunflower is a wellness companion, not a medical provider.
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: spacing.lg, justifyContent: 'center' },

  header: { alignItems: 'center', marginBottom: spacing.xl },
  logo: { fontSize: 72 },
  title: { fontSize: typography.fontSizeXXL, fontWeight: typography.fontWeightBold, color: colors.text, marginTop: spacing.sm },
  subtitle: { fontSize: typography.fontSizeMD, color: colors.textSecondary, marginTop: spacing.xs },

  card: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: spacing.lg,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 1,
    shadowRadius: 12,
    elevation: 4,
    marginBottom: spacing.lg,
  },
  cardTitle: { fontSize: typography.fontSizeLG, fontWeight: typography.fontWeightSemiBold, color: colors.text, marginBottom: spacing.md },
  label: { fontSize: typography.fontSizeSM, fontWeight: typography.fontWeightMedium, color: colors.textSecondary, marginBottom: spacing.xs },
  input: {
    backgroundColor: colors.inputBg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 12,
    fontSize: typography.fontSizeMD,
    color: colors.text,
    marginBottom: spacing.md,
  },
  btn: {
    backgroundColor: colors.primary,
    borderRadius: radius.full,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: spacing.xs,
  },
  btnDisabled: { opacity: 0.6 },
  btnText: { fontSize: typography.fontSizeMD, fontWeight: typography.fontWeightBold, color: colors.textOnPrimary },

  linkRow: { flexDirection: 'row', justifyContent: 'center', marginBottom: spacing.xl },
  linkText: { fontSize: typography.fontSizeSM, color: colors.textSecondary },
  linkBold: { fontWeight: typography.fontWeightSemiBold, color: colors.primaryDark },

  disclaimer: { textAlign: 'center', fontSize: typography.fontSizeXS, color: colors.textMuted },
});
