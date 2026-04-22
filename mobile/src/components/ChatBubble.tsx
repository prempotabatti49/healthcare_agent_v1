import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, radius, typography } from '../theme/colors';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isCrisis?: boolean;
}

export default function ChatBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <View style={[styles.row, isUser ? styles.rowUser : styles.rowAI]}>
      {!isUser && <Text style={styles.avatar}>🌻</Text>}
      <View style={[
        styles.bubble,
        isUser ? styles.bubbleUser : styles.bubbleAI,
        message.isCrisis && styles.bubbleCrisis,
      ]}>
        {message.isCrisis && (
          <Text style={styles.crisisLabel}>⚠️ Crisis support resources included</Text>
        )}
        <Text style={[styles.text, isUser ? styles.textUser : styles.textAI]}>
          {message.content}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', marginBottom: spacing.sm, alignItems: 'flex-end', gap: spacing.xs },
  rowUser: { justifyContent: 'flex-end' },
  rowAI: { justifyContent: 'flex-start' },

  avatar: { fontSize: 22, marginBottom: 2 },

  bubble: {
    maxWidth: '80%', borderRadius: radius.lg, padding: spacing.sm + 2,
  },
  bubbleUser: {
    backgroundColor: colors.bubbleUser,
    borderBottomRightRadius: radius.sm,
  },
  bubbleAI: {
    backgroundColor: colors.bubbleAI,
    borderBottomLeftRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.bubbleAIBorder,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 1,
    shadowRadius: 4,
    elevation: 1,
  },
  bubbleCrisis: {
    borderWidth: 1,
    borderColor: colors.crisis,
    backgroundColor: colors.crisisLight,
  },

  crisisLabel: {
    fontSize: typography.fontSizeXS,
    color: colors.crisis,
    fontWeight: typography.fontWeightSemiBold,
    marginBottom: spacing.xs,
  },

  text: { fontSize: typography.fontSizeMD, lineHeight: 22 },
  textUser: { color: colors.bubbleUserText },
  textAI: { color: colors.bubbleAIText },
});
