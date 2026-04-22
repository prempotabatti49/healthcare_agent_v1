import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, Alert, ScrollView, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '../store/authStore';
import { quotesApi, authApi, HealthQuote } from '../api/client';
import { colors, spacing, radius, typography } from '../theme/colors';

const QUOTE_PREFERENCES = [
  { value: 'daily', label: 'Daily', desc: 'One quote a day' },
  { value: 'weekly', label: 'Weekly', desc: 'Once a week' },
  { value: 'never', label: 'Never', desc: 'No quotes' },
];

export default function ProfileScreen() {
  const { user, logout, refreshUser } = useAuthStore();
  const [quote, setQuote] = useState<HealthQuote | null>(null);
  const [updatingPref, setUpdatingPref] = useState(false);

  useEffect(() => {
    quotesApi.random()
      .then((r) => setQuote(r.data))
      .catch(() => null);
  }, []);

  const handleUpdateQuotePref = async (pref: string) => {
    setUpdatingPref(true);
    try {
      await authApi.updateQuotePreference(pref);
      await refreshUser();
    } catch {
      Alert.alert('Error', 'Could not update preference.');
    } finally {
      setUpdatingPref(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Sign Out', style: 'destructive', onPress: logout },
    ]);
  };

  return (
    <SafeAreaView style={styles.root} edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Avatar + name */}
        <View style={styles.avatarSection}>
          <View style={styles.avatar}>
            <Text style={styles.avatarEmoji}>🌻</Text>
          </View>
          <Text style={styles.name}>{user?.full_name || user?.username}</Text>
          <Text style={styles.email}>{user?.email}</Text>
          <Text style={styles.since}>Member since {user?.created_at?.slice(0, 10)}</Text>
        </View>

        {/* Daily quote card */}
        {quote && (
          <View style={styles.quoteCard}>
            <Text style={styles.quoteText}>"{quote.quote}"</Text>
            {quote.author && <Text style={styles.quoteAuthor}>— {quote.author}</Text>}
          </View>
        )}

        {/* Quote preference */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quote Preference</Text>
          <Text style={styles.sectionDesc}>How often would you like to receive health quotes?</Text>
          <View style={styles.prefRow}>
            {QUOTE_PREFERENCES.map((p) => (
              <TouchableOpacity
                key={p.value}
                style={[styles.prefChip, user?.quote_preference === p.value && styles.prefChipActive]}
                onPress={() => handleUpdateQuotePref(p.value)}
                disabled={updatingPref}
              >
                {updatingPref && user?.quote_preference === p.value
                  ? <ActivityIndicator size="small" color={colors.textOnPrimary} />
                  : (
                    <>
                      <Text style={[styles.prefLabel, user?.quote_preference === p.value && styles.prefLabelActive]}>{p.label}</Text>
                      <Text style={[styles.prefDesc, user?.quote_preference === p.value && styles.prefDescActive]}>{p.desc}</Text>
                    </>
                  )
                }
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Account info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account</Text>
          {[
            { label: 'Username', value: `@${user?.username}` },
            { label: 'Email', value: user?.email ?? '' },
          ].map(({ label, value }) => (
            <View key={label} style={styles.infoRow}>
              <Text style={styles.infoLabel}>{label}</Text>
              <Text style={styles.infoValue}>{value}</Text>
            </View>
          ))}
        </View>

        {/* Disclaimer */}
        <View style={styles.disclaimerBox}>
          <Text style={styles.disclaimerText}>
            🌻 Sunflower is a wellness companion, not a medical provider. Always consult a qualified healthcare professional for medical advice.
          </Text>
        </View>

        {/* Sign out */}
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout} activeOpacity={0.8}>
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.background },
  scroll: { padding: spacing.md, gap: spacing.md },

  avatarSection: { alignItems: 'center', paddingVertical: spacing.lg },
  avatar: {
    width: 88, height: 88, borderRadius: 44,
    backgroundColor: colors.primaryLight, alignItems: 'center', justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  avatarEmoji: { fontSize: 44 },
  name: { fontSize: typography.fontSizeXL, fontWeight: typography.fontWeightBold, color: colors.text },
  email: { fontSize: typography.fontSizeSM, color: colors.textSecondary, marginTop: 2 },
  since: { fontSize: typography.fontSizeXS, color: colors.textMuted, marginTop: 4 },

  quoteCard: {
    backgroundColor: colors.primaryLight, borderLeftWidth: 4, borderLeftColor: colors.primary,
    borderRadius: radius.md, padding: spacing.md,
  },
  quoteText: { fontSize: typography.fontSizeSM, color: colors.text, fontStyle: 'italic', lineHeight: 20 },
  quoteAuthor: { fontSize: typography.fontSizeXS, color: colors.textSecondary, marginTop: spacing.xs },

  section: {
    backgroundColor: colors.card, borderRadius: radius.lg, padding: spacing.md,
    borderWidth: 1, borderColor: colors.border,
  },
  sectionTitle: { fontSize: typography.fontSizeMD, fontWeight: typography.fontWeightSemiBold, color: colors.text, marginBottom: 2 },
  sectionDesc: { fontSize: typography.fontSizeXS, color: colors.textSecondary, marginBottom: spacing.md },

  prefRow: { flexDirection: 'row', gap: spacing.sm },
  prefChip: {
    flex: 1, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md,
    padding: spacing.sm, alignItems: 'center',
  },
  prefChipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  prefLabel: { fontSize: typography.fontSizeSM, fontWeight: typography.fontWeightSemiBold, color: colors.textSecondary },
  prefLabelActive: { color: colors.textOnPrimary },
  prefDesc: { fontSize: typography.fontSizeXS, color: colors.textMuted, marginTop: 2 },
  prefDescActive: { color: colors.textOnPrimary },

  infoRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.divider },
  infoLabel: { fontSize: typography.fontSizeSM, color: colors.textSecondary },
  infoValue: { fontSize: typography.fontSizeSM, color: colors.text, fontWeight: typography.fontWeightMedium },

  disclaimerBox: { backgroundColor: colors.greenLight, borderRadius: radius.md, padding: spacing.md },
  disclaimerText: { fontSize: typography.fontSizeXS, color: colors.green, lineHeight: 18 },

  logoutBtn: {
    borderWidth: 1, borderColor: colors.crisis, borderRadius: radius.full,
    paddingVertical: 14, alignItems: 'center', marginBottom: spacing.xl,
  },
  logoutText: { color: colors.crisis, fontWeight: typography.fontWeightSemiBold, fontSize: typography.fontSizeMD },
});
