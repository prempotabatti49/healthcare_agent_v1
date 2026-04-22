import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator, Alert,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useAuthStore } from '../store/authStore';
import { colors, spacing, radius, typography } from '../theme/colors';
import type { AuthStackParamList } from '../../App';

type Props = { navigation: NativeStackNavigationProp<AuthStackParamList, 'Register'> };

export default function RegisterScreen({ navigation }: Props) {
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const register = useAuthStore((s) => s.register);

  const handleRegister = async () => {
    if (!username.trim() || !email.trim() || !password.trim()) {
      Alert.alert('Missing fields', 'Username, email and password are required.');
      return;
    }
    setLoading(true);
    try {
      await register({ email: email.trim(), username: username.trim(), password, full_name: fullName.trim() || undefined });
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? 'Registration failed. Please try again.';
      Alert.alert('Error', detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.root} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.logo}>🌻</Text>
          <Text style={styles.title}>Join Sunflower</Text>
          <Text style={styles.subtitle}>Start your wellness journey today</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Create your account</Text>

          {[
            { label: 'Full Name (optional)', value: fullName, setter: setFullName, placeholder: 'e.g. Priya Sharma', secure: false },
            { label: 'Username', value: username, setter: setUsername, placeholder: 'e.g. priya_s', secure: false },
            { label: 'Email', value: email, setter: setEmail, placeholder: 'you@example.com', secure: false },
            { label: 'Password', value: password, setter: setPassword, placeholder: 'Choose a password', secure: true },
          ].map(({ label, value, setter, placeholder, secure }) => (
            <React.Fragment key={label}>
              <Text style={styles.label}>{label}</Text>
              <TextInput
                style={styles.input}
                value={value}
                onChangeText={setter}
                placeholder={placeholder}
                placeholderTextColor={colors.textMuted}
                secureTextEntry={secure}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType={label === 'Email' ? 'email-address' : 'default'}
              />
            </React.Fragment>
          ))}

          <TouchableOpacity
            style={[styles.btn, loading && styles.btnDisabled]}
            onPress={handleRegister}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading
              ? <ActivityIndicator color={colors.textOnPrimary} />
              : <Text style={styles.btnText}>Create Account</Text>
            }
          </TouchableOpacity>
        </View>

        <TouchableOpacity onPress={() => navigation.navigate('Login')} style={styles.linkRow}>
          <Text style={styles.linkText}>Already have an account? </Text>
          <Text style={[styles.linkText, styles.linkBold]}>Sign In →</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: spacing.lg, justifyContent: 'center' },
  header: { alignItems: 'center', marginBottom: spacing.xl },
  logo: { fontSize: 64 },
  title: { fontSize: typography.fontSizeXXL, fontWeight: typography.fontWeightBold, color: colors.text, marginTop: spacing.sm },
  subtitle: { fontSize: typography.fontSizeMD, color: colors.textSecondary, marginTop: spacing.xs },
  card: {
    backgroundColor: colors.card, borderRadius: radius.lg, padding: spacing.lg,
    shadowColor: colors.shadow, shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 1, shadowRadius: 12, elevation: 4, marginBottom: spacing.lg,
  },
  cardTitle: { fontSize: typography.fontSizeLG, fontWeight: typography.fontWeightSemiBold, color: colors.text, marginBottom: spacing.md },
  label: { fontSize: typography.fontSizeSM, fontWeight: typography.fontWeightMedium, color: colors.textSecondary, marginBottom: spacing.xs },
  input: {
    backgroundColor: colors.inputBg, borderWidth: 1, borderColor: colors.border,
    borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: 12,
    fontSize: typography.fontSizeMD, color: colors.text, marginBottom: spacing.md,
  },
  btn: { backgroundColor: colors.primary, borderRadius: radius.full, paddingVertical: 14, alignItems: 'center', marginTop: spacing.xs },
  btnDisabled: { opacity: 0.6 },
  btnText: { fontSize: typography.fontSizeMD, fontWeight: typography.fontWeightBold, color: colors.textOnPrimary },
  linkRow: { flexDirection: 'row', justifyContent: 'center' },
  linkText: { fontSize: typography.fontSizeSM, color: colors.textSecondary },
  linkBold: { fontWeight: typography.fontWeightSemiBold, color: colors.primaryDark },
});
