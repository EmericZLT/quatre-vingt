// 卡面资源映射工具
// 实际资源位于 /assets/cards/{Suit}{Rank}.png，例如: SpadeA.png, Heart10.png, JOKER-A.png

export type Rank = '2'|'3'|'4'|'5'|'6'|'7'|'8'|'9'|'10'|'J'|'Q'|'K'|'A'|'JOKER-A'|'JOKER-B'
export type Suit = '♠'|'♥'|'♣'|'♦'|null

/**
 * 根据花色和点数获取卡牌图片路径
 */
export function getCardImage(suit: Suit, rank: Rank): string | null {
  try {
    // 处理JOKER
    if (rank === 'JOKER-A') return `/assets/cards/JOKER-A.png`
    if (rank === 'JOKER-B') return `/assets/cards/JOKER-B.png`
    if (!suit) return null
    
    // 花色映射：♠->Spade, ♥->Heart, ♣->Club, ♦->Diamond
    const suitMap: Record<Exclude<Suit,null>, string> = { 
      '♠': 'Spade', 
      '♥': 'Heart', 
      '♣': 'Club', 
      '♦': 'Diamond' 
    }
    
    // 点数映射（保持原样，首字母大写）
    const rankMap: Record<string, string> = { 
      'J': 'J', 
      'Q': 'Q', 
      'K': 'K', 
      'A': 'A',
      '2': '2',
      '3': '3',
      '4': '4',
      '5': '5',
      '6': '6',
      '7': '7',
      '8': '8',
      '9': '9',
      '10': '10'
    }
    
    const s = suitMap[suit]
    const r = rankMap[rank] || rank
    return `/assets/cards/${s}${r}.png`
  } catch {
    return null
  }
}

/**
 * 解析后端返回的卡牌字符串
 * 格式：普通牌 "2♠", "10♥" 等（rank在前，suit在后）
 *      JOKER "JOKER-A/大王" 或 "JOKER-B/小王"
 */
export function parseCardString(cardStr: string): { suit: Suit; rank: Rank } | null {
  try {
    // 处理JOKER
    if (cardStr.includes('JOKER-A')) {
      return { suit: null, rank: 'JOKER-A' }
    }
    if (cardStr.includes('JOKER-B')) {
      return { suit: null, rank: 'JOKER-B' }
    }
    
    // 解析普通牌：格式为 "rank+suit"，如 "2♠", "10♥", "A♣"
    // 匹配最后一个Unicode字符作为花色
    const suitMatch = cardStr.match(/[♠♥♣♦]$/)
    if (!suitMatch) return null
    
    const suitChar = suitMatch[0] as Exclude<Suit, null>
    const rankStr = cardStr.slice(0, -1) // 去掉最后一个字符（花色）
    
    // 验证rank是否有效
    const validRanks: Rank[] = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    if (!validRanks.includes(rankStr as Rank)) return null
    
    return { suit: suitChar, rank: rankStr as Rank }
  } catch {
    return null
  }
}

/**
 * 从卡牌字符串获取图片路径
 */
export function getCardImageFromString(cardStr: string): string | null {
  const parsed = parseCardString(cardStr)
  if (!parsed) return null
  return getCardImage(parsed.suit, parsed.rank)
}


