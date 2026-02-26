import TelegramBot from 'node-telegram-bot-api';

import { ASSISTANT_NAME } from '../config.js';
import { logger } from '../logger.js';
import { Channel, OnInboundMessage, OnChatMetadata, RegisteredGroup } from '../types.js';

// Telegram JID prefix — distinguishes Telegram chat IDs from WhatsApp JIDs
export const TG_PREFIX = 'tg:';

export function toTgJid(chatId: number | string): string {
  return `${TG_PREFIX}${chatId}`;
}

export function fromTgJid(jid: string): string {
  return jid.startsWith(TG_PREFIX) ? jid.slice(TG_PREFIX.length) : jid;
}

// Telegram message length limit
const TG_MAX_LENGTH = 4096;

function splitMessage(text: string): string[] {
  const chunks: string[] = [];
  let remaining = text;
  while (remaining.length > TG_MAX_LENGTH) {
    // Split at last newline within limit
    let splitAt = remaining.lastIndexOf('\n', TG_MAX_LENGTH);
    if (splitAt <= 0) splitAt = TG_MAX_LENGTH;
    chunks.push(remaining.slice(0, splitAt));
    remaining = remaining.slice(splitAt).trimStart();
  }
  if (remaining.length > 0) chunks.push(remaining);
  return chunks;
}

export interface TelegramChannelOpts {
  token: string;
  onMessage: OnInboundMessage;
  onChatMetadata: OnChatMetadata;
  registeredGroups: () => Record<string, RegisteredGroup>;
}

export class TelegramChannel implements Channel {
  name = 'telegram';

  private bot: TelegramBot;
  private connected = false;
  private opts: TelegramChannelOpts;

  constructor(opts: TelegramChannelOpts) {
    this.opts = opts;
    this.bot = new TelegramBot(opts.token);
  }

  async connect(): Promise<void> {
    this.bot.on('message', (msg) => {
      if (!msg.text) return;

      const chatId = msg.chat.id;
      const jid = toTgJid(chatId);
      const timestamp = new Date(msg.date * 1000).toISOString();
      const isGroup = msg.chat.type === 'group' || msg.chat.type === 'supergroup';
      const chatName = msg.chat.title || msg.chat.username || String(chatId);

      // Always notify metadata for group discovery
      this.opts.onChatMetadata(jid, timestamp, chatName, 'telegram', isGroup);

      // Only deliver full message for registered groups
      const groups = this.opts.registeredGroups();
      if (!groups[jid]) return;

      const sender = String(msg.from?.id || chatId);
      const senderName = [msg.from?.first_name, msg.from?.last_name]
        .filter(Boolean)
        .join(' ') || msg.from?.username || sender;

      const isBotMessage =
        msg.from?.is_bot === true ||
        msg.text.startsWith(`${ASSISTANT_NAME}:`);

      this.opts.onMessage(jid, {
        id: String(msg.message_id),
        chat_jid: jid,
        sender,
        sender_name: senderName,
        content: msg.text,
        timestamp,
        is_from_me: false,
        is_bot_message: isBotMessage,
      });
    });

    this.bot.on('polling_error', (err) => {
      logger.error({ err }, 'Telegram polling error');
    });

    await this.bot.startPolling({ restart: true });
    this.connected = true;
    logger.info('Connected to Telegram');
  }

  async sendMessage(jid: string, text: string): Promise<void> {
    const chatId = fromTgJid(jid);
    const chunks = splitMessage(text);
    for (const chunk of chunks) {
      try {
        await this.bot.sendMessage(Number(chatId) || chatId, chunk);
        logger.info({ jid, length: chunk.length }, 'Telegram message sent');
      } catch (err) {
        logger.error({ jid, err }, 'Failed to send Telegram message');
        throw err;
      }
    }
  }

  isConnected(): boolean {
    return this.connected;
  }

  ownsJid(jid: string): boolean {
    return jid.startsWith(TG_PREFIX);
  }

  async disconnect(): Promise<void> {
    this.connected = false;
    await this.bot.stopPolling();
  }
}
