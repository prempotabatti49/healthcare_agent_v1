import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  Alert, ActivityIndicator, Modal, TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as DocumentPicker from 'expo-document-picker';
import { documentsApi, DocumentOut } from '../api/client';
import { colors, spacing, radius, typography } from '../theme/colors';

const DOC_TYPES = ['medical_report', 'prescription', 'lab_result', 'doctor_notes', 'imaging', 'other'];

const TYPE_EMOJI: Record<string, string> = {
  medical_report: '🏥', prescription: '💊', lab_result: '🧪',
  doctor_notes: '📋', imaging: '🔬', other: '📄',
};

export default function DocumentsScreen() {
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [pickedFile, setPickedFile] = useState<DocumentPicker.DocumentPickerResult | null>(null);
  const [docType, setDocType] = useState('medical_report');
  const [notes, setNotes] = useState('');

  const loadDocs = useCallback(async () => {
    try {
      const res = await documentsApi.list();
      setDocs(res.data);
    } catch {
      Alert.alert('Error', 'Could not load documents.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDocs(); }, [loadDocs]);

  const pickDocument = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ['application/pdf', 'image/*', 'application/vnd.ms-powerpoint',
             'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
      copyToCacheDirectory: true,
    });
    if (!result.canceled) {
      setPickedFile(result);
      setShowModal(true);
    }
  };

  const handleUpload = async () => {
    if (!pickedFile || pickedFile.canceled) return;
    const asset = pickedFile.assets[0];
    setUploading(true);
    try {
      await documentsApi.upload(asset.uri, asset.name, asset.mimeType ?? 'application/octet-stream', docType, notes);
      setShowModal(false);
      setPickedFile(null);
      setNotes('');
      setDocType('medical_report');
      await loadDocs();
      Alert.alert('Success', 'Document uploaded successfully!');
    } catch (err: any) {
      Alert.alert('Upload failed', err?.response?.data?.detail ?? 'Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const renderDoc = ({ item }: { item: DocumentOut }) => (
    <View style={styles.docCard}>
      <Text style={styles.docEmoji}>{TYPE_EMOJI[item.document_type] ?? '📄'}</Text>
      <View style={styles.docInfo}>
        <Text style={styles.docName} numberOfLines={1}>{item.filename}</Text>
        <Text style={styles.docMeta}>{item.document_type.replace('_', ' ')} • {item.created_at.slice(0, 10)}</Text>
        {item.notes ? <Text style={styles.docNotes} numberOfLines={1}>{item.notes}</Text> : null}
      </View>
      {item.is_processed && <Text style={styles.processedBadge}>✓</Text>}
    </View>
  );

  return (
    <SafeAreaView style={styles.root} edges={['top']}>
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>My Documents</Text>
          <Text style={styles.headerSub}>Upload and manage your health records</Text>
        </View>
        <TouchableOpacity style={styles.uploadBtn} onPress={pickDocument} activeOpacity={0.8}>
          <Text style={styles.uploadBtnText}>＋ Upload</Text>
        </TouchableOpacity>
      </View>

      {loading
        ? <ActivityIndicator style={styles.loader} color={colors.primary} size="large" />
        : (
          <FlatList
            data={docs}
            keyExtractor={(d) => d.id}
            renderItem={renderDoc}
            contentContainerStyle={styles.list}
            ListEmptyComponent={
              <View style={styles.empty}>
                <Text style={styles.emptyEmoji}>📂</Text>
                <Text style={styles.emptyTitle}>No documents yet</Text>
                <Text style={styles.emptySub}>Upload your doctor's reports, prescriptions and lab results so Sunflower can give you personalised guidance.</Text>
              </View>
            }
          />
        )
      }

      {/* Upload modal */}
      <Modal visible={showModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Upload Document</Text>
            {pickedFile && !pickedFile.canceled && (
              <Text style={styles.fileName} numberOfLines={1}>{pickedFile.assets[0].name}</Text>
            )}

            <Text style={styles.label}>Document Type</Text>
            <View style={styles.typeGrid}>
              {DOC_TYPES.map((t) => (
                <TouchableOpacity
                  key={t}
                  style={[styles.typeChip, docType === t && styles.typeChipActive]}
                  onPress={() => setDocType(t)}
                >
                  <Text style={[styles.typeChipText, docType === t && styles.typeChipTextActive]}>
                    {TYPE_EMOJI[t]} {t.replace('_', ' ')}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.label}>Notes (optional)</Text>
            <TextInput
              style={styles.notesInput}
              value={notes}
              onChangeText={setNotes}
              placeholder="e.g. Ayurvedic consultation, June 2024"
              placeholderTextColor={colors.textMuted}
              multiline
            />

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setShowModal(false)}>
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.confirmBtn, uploading && styles.btnDisabled]}
                onPress={handleUpload}
                disabled={uploading}
              >
                {uploading
                  ? <ActivityIndicator color={colors.textOnPrimary} />
                  : <Text style={styles.confirmBtnText}>Upload</Text>
                }
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    padding: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border,
    backgroundColor: colors.card,
  },
  headerTitle: { fontSize: typography.fontSizeLG, fontWeight: typography.fontWeightBold, color: colors.text },
  headerSub: { fontSize: typography.fontSizeXS, color: colors.textSecondary },
  uploadBtn: { backgroundColor: colors.primary, borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: 8 },
  uploadBtnText: { fontWeight: typography.fontWeightBold, color: colors.textOnPrimary, fontSize: typography.fontSizeSM },

  loader: { marginTop: spacing.xxl },
  list: { padding: spacing.md, gap: spacing.sm },

  docCard: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    backgroundColor: colors.card, borderRadius: radius.md, padding: spacing.md,
    borderWidth: 1, borderColor: colors.border,
  },
  docEmoji: { fontSize: 28 },
  docInfo: { flex: 1 },
  docName: { fontSize: typography.fontSizeMD, fontWeight: typography.fontWeightMedium, color: colors.text },
  docMeta: { fontSize: typography.fontSizeXS, color: colors.textSecondary, marginTop: 2 },
  docNotes: { fontSize: typography.fontSizeXS, color: colors.textMuted, marginTop: 2, fontStyle: 'italic' },
  processedBadge: { fontSize: 16, color: colors.green },

  empty: { alignItems: 'center', paddingTop: spacing.xxl, paddingHorizontal: spacing.xl },
  emptyEmoji: { fontSize: 64, marginBottom: spacing.md },
  emptyTitle: { fontSize: typography.fontSizeLG, fontWeight: typography.fontWeightSemiBold, color: colors.text },
  emptySub: { textAlign: 'center', fontSize: typography.fontSizeSM, color: colors.textSecondary, marginTop: spacing.sm, lineHeight: 20 },

  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: colors.card, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg },
  modalTitle: { fontSize: typography.fontSizeXL, fontWeight: typography.fontWeightBold, color: colors.text, marginBottom: spacing.sm },
  fileName: { fontSize: typography.fontSizeSM, color: colors.textSecondary, marginBottom: spacing.md, fontStyle: 'italic' },
  label: { fontSize: typography.fontSizeSM, fontWeight: typography.fontWeightMedium, color: colors.textSecondary, marginBottom: spacing.xs, marginTop: spacing.sm },

  typeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  typeChip: { borderWidth: 1, borderColor: colors.border, borderRadius: radius.full, paddingHorizontal: 10, paddingVertical: 5 },
  typeChipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  typeChipText: { fontSize: typography.fontSizeXS, color: colors.textSecondary },
  typeChipTextActive: { color: colors.textOnPrimary, fontWeight: typography.fontWeightSemiBold },

  notesInput: {
    backgroundColor: colors.inputBg, borderWidth: 1, borderColor: colors.border,
    borderRadius: radius.md, padding: spacing.sm, color: colors.text,
    fontSize: typography.fontSizeSM, minHeight: 72, textAlignVertical: 'top',
  },

  modalActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.lg },
  cancelBtn: { flex: 1, borderWidth: 1, borderColor: colors.border, borderRadius: radius.full, paddingVertical: 12, alignItems: 'center' },
  cancelBtnText: { color: colors.textSecondary, fontWeight: typography.fontWeightMedium },
  confirmBtn: { flex: 2, backgroundColor: colors.primary, borderRadius: radius.full, paddingVertical: 12, alignItems: 'center' },
  confirmBtnText: { color: colors.textOnPrimary, fontWeight: typography.fontWeightBold },
  btnDisabled: { opacity: 0.6 },
});
