/**
 * @file Define os tipos de dados para o módulo de resumos.
 */

export interface Summary {
  id: string;
  title: string;
  description: string;
  content: string; // O template da mensagem para o WhatsApp
}
