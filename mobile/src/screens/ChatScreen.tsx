import React, { useState, useRef, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, KeyboardAvoidingView,
  Platform, ActivityIndicator, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { chatApi } from '../api/client';
import { colors, spacing, typography, radius } from '../theme/colors';
import ChatBubble from '../components/ChatBubble';
import MessageInput from '../components/MessageInput';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isCrisis?: boolean;
}

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm Sunflower 🌻, your personal health companion. How are you feeling today? You can ask me anything about your health, share how you're feeling, or upload your medical reports.",
    },
  ]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [sending, setSending] = useState(false);
  const listRef = useRef<FlatList>(null);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || sending) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setSending(true);

    try {
      const res = await chatApi.sendMessage(text.trim(), conversationId);
      const data = res.data;
      setConversationId(data.conversation_id);
      const aiMsg: Message = {
        id: data.message_id,
        role: 'assistant',
        content: data.response,
        isCrisis: data.was_crisis_flagged,
      };
      setMessages((prev) => [...prev, aiMsg]);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? 'Something went wrong. Please try again.';
      Alert.alert('Error', detail);
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    } finally {
      setSending(false);
    }
  }, [conversationId, sending]);

  return (
    <SafeAreaView style={styles.root} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerEmoji}>🌻</Text>
        <View>
          <Text style={styles.headerTitle}>Sunflower</Text>
          <Text style={styles.headerSub}>Your wellness companion</Text>
        </View>
      </View>

      {/* Watermark */}
      <Text style={styles.watermark}>🌻</Text>

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(m) => m.id}
          renderItem={({ item }) => <ChatBubble message={item} />}
          contentContainerStyle={styles.listContent}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: false })}
          showsVerticalScrollIndicator={false}
        />

        {sending && (
          <View style={styles.typingRow}>
            <ActivityIndicator size="small" color={colors.primary} />
            <Text style={styles.typingText}>Sunflower is thinking…</Text>
          </View>
        )}

        <MessageInput onSend={sendMessage} disabled={sending} />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.background },
  flex: { flex: 1 },

  header: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    borderBottomWidth: 1, borderBottomColor: colors.border,
    backgroundColor: colors.card,
  },
  headerEmoji: { fontSize: 32 },
  headerTitle: { fontSize: typography.fontSizeLG, fontWeight: typography.fontWeightBold, color: colors.text },
  headerSub: { fontSize: typography.fontSizeXS, color: colors.textSecondary },

  watermark: {
    position: 'absolute', fontSize: 280, opacity: 0.03,
    top: '30%', alignSelf: 'center', zIndex: 0, pointerEvents: 'none',
  },

  listContent: { padding: spacing.md, paddingBottom: spacing.sm },

  typingRow: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    paddingHorizontal: spacing.lg, paddingBottom: spacing.xs,
  },
  typingText: { fontSize: typography.fontSizeSM, color: colors.textSecondary, fontStyle: 'italic' },
});
