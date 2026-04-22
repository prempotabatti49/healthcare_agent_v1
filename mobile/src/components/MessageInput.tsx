import React, { useState } from 'react';
import {
  View, TextInput, TouchableOpacity, StyleSheet, Alert, Text,
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { documentsApi } from '../api/client';
import { colors, spacing, radius, typography } from '../theme/colors';

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export default function MessageInput({ onSend, disabled }: Props) {
  const [text, setText] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleSend = () => {
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText('');
  };

  const handleAttach = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ['application/pdf', 'image/*'],
      copyToCacheDirectory: true,
    });
    if (result.canceled) return;

    const asset = result.assets[0];
    setUploading(true);
    try {
      await documentsApi.upload(asset.uri, asset.name, asset.mimeType ?? 'application/octet-stream', 'other', '');
      Alert.alert('Uploaded', `"${asset.name}" has been added to your health records.`);
      onSend(`I've just uploaded a document: ${asset.name}`);
    } catch {
      Alert.alert('Upload failed', 'Could not upload the document. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[styles.iconBtn, (disabled || uploading) && styles.disabled]}
        onPress={handleAttach}
        disabled={disabled || uploading}
        activeOpacity={0.7}
      >
        <Text style={styles.iconBtnText}>{uploading ? '⏳' : '📎'}</Text>
      </TouchableOpacity>

      <TextInput
        style={styles.input}
        value={text}
        onChangeText={setText}
        placeholder="How are you feeling today?"
        placeholderTextColor={colors.textMuted}
        multiline
        maxLength={2000}
        editable={!disabled}
        returnKeyType="default"
      />

      <TouchableOpacity
        style={[styles.sendBtn, (!text.trim() || disabled) && styles.sendBtnDisabled]}
        onPress={handleSend}
        disabled={!text.trim() || disabled}
        activeOpacity={0.8}
      >
        <Text style={styles.sendIcon}>↑</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row', alignItems: 'flex-end', gap: spacing.xs,
    padding: spacing.sm, paddingHorizontal: spacing.md,
    borderTopWidth: 1, borderTopColor: colors.border,
    backgroundColor: colors.card,
  },

  iconBtn: {
    width: 40, height: 40, borderRadius: radius.full,
    backgroundColor: colors.inputBg, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: colors.border,
  },
  iconBtnText: { fontSize: 18 },

  input: {
    flex: 1, minHeight: 40, maxHeight: 120,
    backgroundColor: colors.inputBg,
    borderWidth: 1, borderColor: colors.border,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    fontSize: typography.fontSizeMD, color: colors.text,
  },

  sendBtn: {
    width: 40, height: 40, borderRadius: radius.full,
    backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center',
  },
  sendBtnDisabled: { opacity: 0.4 },
  sendIcon: { fontSize: 20, color: colors.textOnPrimary, fontWeight: typography.fontWeightBold },

  disabled: { opacity: 0.4 },
});
