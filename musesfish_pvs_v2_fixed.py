#!/usr/bin/env pypy
# -*- coding: utf-8 -*-

#Updated by Si Miao 2021/05/20
from __future__ import print_function
import re, sys, time
from itertools import count
from collections import namedtuple
import random
from board import board
from board import common_v2_fixed as common
from copy import deepcopy
import os
# import readline
os.system('@echo off')


B = board.Board()
piece = {'P': 44, 'N': 108, 'B': 23, 'R': 233, 'A': 23, 'C': 101, 'K': 2500}
put = lambda board, i, p: board[:i] + p + board[i+1:]
r = {'R': 2, 'N': 2, 'B': 2, 'A': 2, 'C': 2, 'P': 5}
b = {'r': 2, 'n': 2, 'b': 2, 'a': 2, 'c': 2, 'p': 5}
di = {True: deepcopy(r), False: deepcopy(b)}
# 子力价值表参考“象眼”
cache = {}
forbidden_moves = set()


def resetrbdict():
    global r, b, di
    r = {'R': 2, 'N': 2, 'B': 2, 'A': 2, 'C': 2, 'P': 5}
    b = {'r': 2, 'n': 2, 'b': 2, 'a': 2, 'c': 2, 'p': 5}
    di = {True: deepcopy(r), False: deepcopy(b)}


pst = deepcopy(common.pst)
discount_factor = common.discount_factor

A0, I0, A9, I9 = 12 * 16 + 3, 12 * 16 + 11, 3 * 16 + 3,  3 * 16 + 11

'''
D: 暗车
E: 暗马
F: 暗相
G: 暗士
H: 暗炮
I: 暗车
'''

initial = (
    '               \n'  # 0
    '               \n'  # 1
    '               \n'  # 2
    '   rnbakabnr   \n'  # 3
    '   .........   \n'  # 4
    '   .c.....c.   \n'  # 5
    '   p.p.p.p.p   \n'  # 6
    '   .........   \n'  # 7
    '   .........   \n'  # 8
    '   P.P.P.P.P   \n'  # 9
    '   .C.....C.   \n'  # 10
    '   .........   \n'  # 11
    '   RNBAKABNR   \n'  # 12
    '               \n'  # 13
    '               \n'  # 14
    '               \n'  # 15
)

initial_covered = (
    '               \n'  # 0
    '               \n'  # 1
    '               \n'  # 2
    '   defgkgfed   \n'  # 3
    '   .........   \n'  # 4
    '   .h.....h.   \n'  # 5
    '   i.i.i.i.i   \n'  # 6
    '   .........   \n'  # 7
    '   .........   \n'  # 8
    '   I.I.I.I.I   \n'  # 9
    '   .H.....H.   \n'  # 10
    '   .........   \n'  # 11
    '   DEFGKGFED   \n'  # 12
    '               \n'  # 13
    '               \n'  # 14
    '               \n'  # 15
)


# Lists of possible moves for each piece type.
N, E, S, W = -16, 1, 16, -1
directions = {
    'P': (N, W, E),
    'I': (N, ), #暗兵
    'N': (N+N+E, E+N+E, E+S+E, S+S+E, S+S+W, W+S+W, W+N+W, N+N+W),
    'E': (N+N+E, E+N+E, W+N+W, N+N+W), #暗马
    'B': (2 * N + 2 * E, 2 * S + 2 * E, 2 * S + 2 * W, 2 * N + 2 * W),
    'F': (2 * N + 2 * E, 2 * N + 2 * W), #暗相
    'R': (N, E, S, W),
    'D': (N, E, W), #暗车
    'C': (N, E, S, W),
    'H': (N, E, S, W), #暗炮
    'A': (N+E, S+E, S+W, N+W),
    'G': (N+E, N+W), #暗士
    'K': (N, E, S, W)
}

uni_pieces = {
    '.': '．',
    'R': '\033[31m俥\033[0m',
    'N': '\033[31m傌\033[0m',
    'B': '\033[31m相\033[0m',
    'A': '\033[31m仕\033[0m',
    'K': '\033[31m帅\033[0m',
    'P': '\033[31m兵\033[0m',
    'C': '\033[31m炮\033[0m',
    'D': '\033[31m暗\033[0m',
    'E': '\033[31m暗\033[0m',
    'F': '\033[31m暗\033[0m',
    'G': '\033[31m暗\033[0m',
    'H': '\033[31m暗\033[0m',
    'I': '\033[31m暗\033[0m',
    'r': '车',
    'n': '马',
    'b': '象',
    'a': '士',
    'k': '将',
    'p': '卒',
    'c': '炮',
    'd': '暗',
    'e': '暗',
    'f': '暗',
    'g': '暗',
    'h': '暗',
    'i': '暗'
}

MATE_LOWER = piece['K'] - (2*piece['R'] + 2*piece['N'] + 2*piece['B'] + 2*piece['A'] + 2*piece['C'] + 5*piece['P'])
MATE_UPPER = piece['K'] + (2*piece['R'] + 2*piece['N'] + 2*piece['B'] + 2*piece['A'] + 2*piece['C'] + 5*piece['P'])

# The table size is the maximum number of elements in the transposition table.
TABLE_SIZE = 1e7

# Constants for tuning search
QS_LIMIT = 219
EVAL_ROUGHNESS = 13
DRAW_TEST = True
THINK_TIME = 1


###############################################################################
# Mapping
# To be more convenient, we initialize the mapping as a global const dictionary
###############################################################################
mapping = {}
average = {}


###############################################################################
# Chess logic
###############################################################################

class Position(namedtuple('Position', 'board score turn')):
    """ A state of a chess game
    board -- a 256 char representation of the board
    score -- the board evaluation
    """

    def set(self):
        self.che = 0
        self.che_opponent = 0
        return self

    def gen_moves(self):
        # For each of our pieces, iterate through each possible 'ray' of moves,
        # as defined in the 'directions' map. The rays are broken e.g. by
        # captures or immediately in case of pieces such as knights.
        for i in range(51, 204):

            p = self.board[i]
            if not p.isupper() or p == 'U': continue

            if p == 'K': 
                for scanpos in range(i - 16, A9, -16):
                    if self.board[scanpos] == 'k':
                        yield (i,scanpos)
                    elif self.board[scanpos] != '.':
                        break

            if p == 'R':
                self.che += 1

            if p == 'r':
                self.che_opponent += 1

            if p in ('C', 'H'): #明暗炮
                for d in directions[p]:
                    cfoot = 0
                    for j in count(i+d, d):
                        q = self.board[j]
                        if q.isspace():break
                        if cfoot == 0 and q == '.':yield (i,j)
                        elif cfoot == 0 and q != '.':cfoot += 1
                        elif cfoot == 1 and q.islower(): yield (i,j);break
                        elif cfoot == 1 and q.isupper(): break;
                continue

            for d in directions[p]:
                for j in count(i+d, d):
                    q = self.board[j]
                    # Stay inside the board, and off friendly pieces
                    if q.isspace() or q.isupper(): break
                    # 过河的卒/兵才能横着走
                    if p == 'P' and d in (E, W) and i > 128: break
                    # j & 15 等价于 j % 16但是更快
                    elif p == 'K' and (j < 160 or j & 15 > 8 or j & 15 < 6): break
                    elif p == 'G' and j != 183: break #暗士, 花心坐标: (11, 7), 11 * 16 + 7 = 183
                    elif p in ('N', 'E'): #暗马
                        n_diff_x = (j - i) & 15
                        if n_diff_x == 14 or n_diff_x == 2:
                            if self.board[i + (1 if n_diff_x == 2 else -1)] != '.': break
                        else:
                            if j > i and self.board[i + 16] != '.': break
                            elif j < i and self.board[i - 16] != '.': break
                    elif p in ('B', 'F') and self.board[i + d // 2] != '.':break
                    # Move it
                    yield (i, j)
                    # Stop crawlers from sliding, and sliding after captures
                    if p in 'PNBAKIEFG' or q.islower(): break

    def rotate(self):
        ''' Rotates the board, preserving enpassant '''
        p = Position(
            self.board[-2::-1].swapcase() + " ", -self.score, not self.turn)
        p.set()
        return p

    @staticmethod
    def rotate_new(board, score, turn):
        p = Position(
            board[-2::-1].swapcase() + " ", -score, not turn)
        p.set()
        return p

    def nullmove(self):
        ''' Like rotate, but clears ep and kp '''
        return self.rotate()

    def move(self, move):
        i, j = move
        # Copy variables and reset ep and kp
        score = self.score + self.value(move)
        # Actual move
        if self.board[i] in 'RNBAKCP':
            board = put(self.board, j, self.board[i])
        else:
            board = put(self.board, j, 'U')
        board = put(board, i, '.')
        return Position.rotate_new(board, score, self.turn)

    def mymove_check(self, move, discount_red=True, discount_black=False):
        i, j = move
        # Copy variables and reset ep and kp
        ############################################################################
        # TODO: Evaluate the score of each move!
        # The following line is NOT implemented. However, it is extremely important!
        # score = self.score + self.value(move)
        ############################################################################
        # Actual move
        # put = lambda board, i, p: board[:i] + p + board[i + 1:]
        eat = self.board[j]
        dst = None

        checkmate = False
        if self.board[j] == 'k':
            checkmate = True

        if self.board[j] in "defghi":
            dst = None
            if self.turn:
                dst = mapping[j]
            else:
                dst = mapping[254-j]
            # 这里是吃暗子的逻辑
            # 在这个简易程序中，假设AI执黑，玩家执红。
            # 那么AI其实是不知道玩家吃了自己什么暗子的
            # 因此在玩家执红吃黑暗子时，黑方的暗子集合并不会更新。
            # 本程序设置了discount_red/black开关处理这一逻辑。
            if self.turn:
               if discount_black:
                   dst2 = dst.lower()
                   di[False][dst2] -= 1
            else:
               if discount_red: #2021/05/25 BUGGY!!!!!!!!!!!!!!!!
                    dst2 = dst.upper()
                    di[True][dst2] -= 1

        if self.board[i] in "RNBAKCP":
            board = put(self.board, j, self.board[i])
        else:
            if self.turn:
                board = put(self.board, j, mapping[i])
                dst2 = mapping[i].upper()
                di[True][dst2] -= 1
            else:
                board = put(self.board, j, mapping[254-i].upper())
                dst2 = mapping[254-i].lower()
                di[False][dst2] -= 1
        board = put(board, i, '.')

        return Position.rotate_new(board, self.score, self.turn), checkmate, eat, dst

    def value(self, move):
        i, j = move
        p, q = self.board[i], self.board[j].upper()
        # Actual move
        if p == 'H' and ((i == 164 and j == 52 and self.board[51] in 'dr') or (i == 170 and j == 58 and self.board[59] in 'dr')):   # TODO: 使用更智能的方式处理博子
            if self.che < self.che_opponent:
                return -200
            if self.che == self.che_opponent:
                if (i == 164 and self.board[148] in 'pr') or (i == 170 and self.board[154] in 'pr'):
                    return 100
                else:
                    return -100

        if q == 'K':
            return 3500
        if p in 'RNBAKCP':
            score = pst[p][j] - pst[p][i]  # 这里有一个隐藏的很深的BUG。如果对手走出将帅对饮的一步棋，score应该很高(因为直接赢棋)。但由于减了pst[p][i], 减了自己的皇上，所以代码中的score是接近0的。
            # 因此，当对方是老将时应直接返回最大值，不能考虑己方。
            if p == 'C' and i & 15 == 7 and j & 15 != 7:
                cnt = 0
                # j & 15 ！= 7很重要，如果没有这句话，AI就不停地直线走来走去赚空头炮积分
                for scanpos in range(i - 16, A9, -16):
                    if self.board[scanpos] == 'k':
                        score -= 70  # 空头炮奖励
                        if cnt >= 4 or self.che > 0:
                            score -= 30
                    elif self.board[scanpos] != '.':
                        break
                    cnt += 1

            if p == 'C' and i & 15 != 7 and j & 15 == 7:
                cnt = 0
                # i & 15 ！= 7很重要，如果没有这句话，AI就不停地直线走来走去赚空头炮积分
                for scanpos in range(j - 16, A9, -16):
                    if self.board[scanpos] == 'k':
                        score += 70  # 空头炮奖励
                        if cnt >= 4 or self.che > 0:
                            score += 30
                    elif self.board[scanpos] != '.':
                        break
        else:
            # 不确定明子的平均价值计算算法:
            # 假设某一方可能的暗子是 两车一炮。
            # 则在某位置处不确定明子的价值为 (车在该处的价值*2 + 炮在该处的价值)/(2+1)。
            # 为了加速计算，这一数值已经被封装到了average这一字典中并预先计算(Pre-compute)。
            score = average[self.turn][True][j] - average[self.turn][False]  # 相应位置不确定明子的平均价值 - 暗子
            if p == 'D':
               key = 'R' if not self.turn else 'r'  # 对方车
               score -= (20+40*(di[not self.turn][key]+self.che_opponent))  # 暗车溜出，扣分! 扣的分数和对方剩余车的个数有关
            if p == 'I':
                if self.board[i - 32] in 'rp':  # 原先是RP, 这是个BUG!现解决
                    score -= average[self.turn][False] // 3
                elif self.board[i - 32] == 'n':  # 之前是N, 不正确，已更正!
                    score += 40
                else:
                    score += 20

        # Capture
        if q.isupper():
            k = 254 - j
            if q in 'RNBAKCP':
                score += pst[q][k]
            else:
                score += average[not self.turn][False]
                if q == 'D':
                    key = 'R' if self.turn else 'r'  # 己方暗车
                    score += (20 + 40*(di[self.turn][key]+self.che))  # 吃对方暗车，加分! 加的分数和己方剩余车的个数相关，如果本方没有车了，那吃个暗车不算太大的收益

        return score

###############################################################################
# Search logic
###############################################################################

# lower <= s(pos) <= upper
Entry = namedtuple('Entry', 'lower upper')


class Searcher:
    def __init__(self):
        self.tp_score = {}
        self.tp_move = {}
        self.history = set()
        self.nodes = 0
        self.average = {}

    def alphabeta(self, pos, alpha, beta, depth, root=True):
        """ returns r where
                s(pos) <= r < gamma    if gamma > s(pos)
                gamma <= r <= s(pos)   if gamma <= s(pos)"""
        if root:
            self.tp_score = {}
            self.tp_move = {}
        self.nodes += 1

        # Depth <= 0 is QSearch. Here any position is searched as deeply as is needed for
        # calmness, and from this point on there is no difference in behaviour depending on
        # depth, so so there is no reason to keep different depths in the transposition table.
        depth = max(depth, 0)

        # Sunfish is a king-capture engine, so we should always check if we
        # still have a king. Notice since this is the only termination check,
        # the remaining code has to be comfortable with being mated, stalemated
        # or able to capture the opponent king.
        if pos.score <= -MATE_LOWER:
            return -MATE_UPPER

        # We detect 3-fold captures by comparing against previously
        # _actually played_ positions.
        # Note that we need to do this before we look in the table, as the
        # position may have been previously reached with a different score.
        # This is what prevents a search instability.
        # FIXME: This is not true, since other positions will be affected by
        # the new values for all the drawn positions.
        if DRAW_TEST:
            if not root and pos in self.history:
                return 0

        # Look in the table if we have already searched this position before.
        # We also need to be sure, that the stored search was over the same
        # nodes as the current search.
        entry = self.tp_score.get((pos, depth, root), Entry(-MATE_UPPER, MATE_UPPER))
        if entry.lower >= beta and (not root or self.tp_move.get(pos) is not None):
            return entry.lower
        if entry.upper < alpha:
            return entry.upper

        # Here extensions may be added
        # Such as 'if in_check: depth += 1'

        # Generator of moves to search in order.
        # This allows us to define the moves, but only calculate them if needed.
            # First try not moving at all. We only do this if there is at least one major
            # piece left on the board, since otherwise zugzwangs are too dangerous.
        if depth > 0 and not root and any(c in pos.board for c in 'RNC'):
            val = -self.alphabeta(pos.nullmove(), -beta,1-beta, depth-3, root=False)
            if val >= beta and self.alphabeta(pos,alpha,beta,depth - 3,root=False):
               #print("depth=%s, Return from nullmove! val=%s"%(depth, val))
               return val
        # For QSearch we have a different kind of null-move, namely we can just stop
        # and not capture anything else.
        if depth == 0:
            return pos.score
        # Then killer move. We search it twice, but the tp will fix things for us.
        # Note, we don't have to check for legality, since we've already done it
        # before. Also note that in QS the killer must be a capture, otherwise we
        # will be non deterministic.
        best = -MATE_UPPER
        killer = self.tp_move.get(pos)

        # Then all the other moves
        mvBest = None
        for move in [killer] + sorted(pos.gen_moves(), key=pos.value, reverse=True):
        #for val, move in sorted(((pos.value(move), move) for move in pos.gen_moves()), reverse=True):
            # If depth == 0 we only try moves with high intrinsic score (captures and
            # promotions). Otherwise we do all moves.
            #print(depth, move)
            if (move is not None) and (depth > 0):
                if best == -MATE_UPPER:
                    val = -self.alphabeta(pos.move(move), -beta, -alpha, depth - 1, root=False)
                else:
                    val = -self.alphabeta(pos.move(move), -alpha - 1, -alpha, depth - 1, root=False)
                    if val > alpha and val < beta:
                        val = -self.alphabeta(pos.move(move), -beta, -alpha, depth - 1, root=False)
                if val > best:
                    best = val
                    if val > beta:
                        mvBest = move
                        break
                    if val > alpha:
                        alpha = val
                        mvBest = move
        if mvBest is not None:
            # Clear before setting, so we always have a value
            # Save the move for pv construction and killer heuristic
            if len(self.tp_move) > TABLE_SIZE: self.tp_move.clear()
            self.tp_move[pos] = mvBest

        # Stalemate checking is a bit tricky: Say we failed low, because
        # we can't (legally) move and so the (real) score is -infty.
        # At the next depth we are allowed to just return r, -infty <= r < gamma,
        # which is normally fine.
        # However, what if gamma = -10 and we don't have any legal moves?
        # Then the score is actaully a draw and we should fail high!
        # Thus, if best < gamma and best < 0 we need to double check what we are doing.
        # This doesn't prevent sunfish from making a move that results in stalemate,
        # but only if depth == 1, so that's probably fair enough.
        # (Btw, at depth 1 we can also mate without realizing.)
        if best < alpha and best < 0 and depth > 0:
            is_dead = lambda pos: any(pos.value(m) >= MATE_LOWER for m in pos.gen_moves())
            if all(is_dead(pos.move(m)) for m in pos.gen_moves()):
                in_check = is_dead(pos.nullmove())
                best = -MATE_UPPER if in_check else 0

        # Clear before setting, so we always have a value
        if len(self.tp_score) > TABLE_SIZE: self.tp_score.clear()
        # Table part 2
        if best >= beta:
            self.tp_score[pos, depth, root] = Entry(best, entry.upper)
        if best < alpha:
            self.tp_score[pos, depth, root] = Entry(entry.lower, best)

        return best

    def search(self, pos, history=()):
        """ Iterative deepening MTD-bi search """
        self.nodes = 0
        self.calc_average()
        if DRAW_TEST:
            self.history = set(history)
            # print('# Clearing table due to new history')
            self.tp_score.clear()

        # In finished games, we could potentially go far enough to cause a recursion
        # limit exception. Hence we bound the ply.
        for depth in range(6, 8):
            # The inner loop is a binary search on the score of the position.
            # Inv: lower <= score <= upper
            # 'while lower != upper' would work, but play tests show a margin of 20 plays
            # better.
            lower, upper = -MATE_UPPER, MATE_UPPER
            self.alphabeta(pos, lower, upper, depth)
            yield depth, self.tp_move.get(pos), self.tp_score.get((pos, depth, True), Entry(-MATE_UPPER, MATE_UPPER)).lower

    def calc_average(self):
        global average

        numr, numb = sum(r[key] for key in r), sum(b[key] for key in b)
        averagecoveredr, averagecoveredb = 0, 0
        averager, averageb = {}, {}

        if numr == 0:
            averagecoveredr = 0
            for i in range(51, 204):
                averager[i] = 0

        else:
            sumr = 0
            for key in r.keys():
                sumr += pst["1"][key] * r[key] / discount_factor
            averagecoveredr = int(sumr//numr)

            for i in range(51, 204):
                sumr = 0
                for key in r.keys():
                    sumr += pst[key][i] * r[key]
                averager[i] = sumr//numr

        if numb == 0:
            averagecoveredb = 0
            for i in range(51, 204):
                averageb[i] = 0

        else:
            sumb = 0
            for key in b.keys():
                sumb += pst["1"][key.swapcase()] * b[key] / discount_factor
            averagecoveredb = int(sumb//numb)

            for i in range(51, 204):
                sumb = 0
                for key in b.keys():
                    sumb += pst[key.swapcase()][i] * b[key]
                averageb[i] = sumb//numb

        self.average = {True: {False: averagecoveredr, True: averager}, False: {False: averagecoveredb, True: averageb}}
        average = deepcopy(self.average)
        return self.average

###############################################################################
# User interface
###############################################################################


def parse(c):
    fil, rank = ord(c[0]) - ord('a'), int(c[1])
    return A0 + fil - 16*rank


def render(i):
    rank, fil = divmod(i - A0, 16)
    return chr(fil + ord('a')) + str(-rank)


def render_tuple(t):
    return render(t[0]) + render(t[1])


def print_pos(pos):
    chessstr = ''
    for i, row in enumerate(pos.board.split()):
        joinstr = ''.join(uni_pieces.get(p, p) for p in row)
        print(' ', 9 - i, joinstr)
        chessstr += (' ' + str(9 - i) + joinstr)
    print('    ａｂｃｄｅｆｇｈｉ\n\n')
    chessstr += '    ａｂｃｄｅｆｇｈｉ\n\n\n'
    return chessstr


def random_policy(pos):
    '''
    A test function that generates a random policy
    '''
    all_moves = list(pos.gen_moves())
    stupid_AI_move = random.choice(all_moves)
    return stupid_AI_move


def translate_eat(eat, dst, turn, type):
    assert turn in {'RED', 'BLACK'} and type in {'CLEARMODE', 'DARKMODE'}
    if eat == '.':
        return None
    if turn == 'BLACK':
        eat = eat.swapcase()
    if type == 'DARKMODE':
        return uni_pieces[eat]
    else:
        if dst is None:  # 吃明子
            return uni_pieces[eat]
        else:  # 吃暗子
            dst = uni_pieces[dst]
            if turn == 'RED':
                dst += "(暗)"
            else:
                dst += "\033[31m(暗)\033[0m"
            return dst


def main(random_move=False, AI=True):
    global mapping
    resetrbdict()
    mapping = B.translate_mapping(B.mapping)

    '''
    while True:
        mapping = B.translate_mapping(B.mapping)
        R, BL = {}, {}
        for map in mapping:
            if mapping[map].isupper():
                if mapping[map] in R:
                    R[mapping[map]] += 1
                else:
                    R[mapping[map]] = 1
            if mapping[map].islower():
                if mapping[map] in BL:
                    BL[mapping[map]] += 1
                else:
                    BL[mapping[map]] = 1
        assert R == r and BL == b
        print("CHECKED!")
    '''

    hist = [Position(initial_covered, 0, True).set()]
    searcher = Searcher()
    searcher.calc_average()
    myeatlist = []
    AIeatlist = []

    while True:
        print("\033[31m玩家吃子\033[0m: " + " ".join(myeatlist))
        print("电脑吃子:" + " " + " ".join(AIeatlist))
        print(di)
        #print(average)
        print_pos(hist[-1])
        #print(hist[-1].turn, hist[-1].score)

        if hist[-1].score <= -MATE_LOWER:
            print("You lost")
            break

        # We query the user until she enters a (pseudo) legal move.
        move = None
        genmoves = set(hist[-1].gen_moves())
        while move not in genmoves:
            inp = input('Your move: ').strip()
            if inp.upper() == 'R':
                print("You resign!")
                exit(0)
            match = re.match('([a-i][0-9])'*2, inp)
            if match:
                move = parse(match.group(1)), parse(match.group(2))
                if inp.upper() == 'R':
                    print("You RESIGNED!")
                    break

            else:
                # Inform the user when invalid input (e.g. "help") is entered
                print("Please enter a move like h2e2")

        pos, win, eat, dst = hist[-1].mymove_check(move)

        if win:
            print("You win!")
            break

        rendered_eat = translate_eat(eat, dst, "RED", "CLEARMODE")
        if rendered_eat:
            myeatlist.append(rendered_eat)

        hist.append(pos) #move的过程Rotate了一次

        # After our move we rotate the board and print it again.
        # This allows us to see the effect of our move.
        print("\033[31m玩家吃子\033[0m:" + " ".join(myeatlist))
        print("电脑吃子:" + " " + " ".join(AIeatlist))
        print(di)
        #print(average)
        print_pos(hist[-1].rotate())
        #print(hist[-1].turn, hist[-1].score)

        if hist[-1].score <= -MATE_LOWER:
            print("You win!")
            break

        # Fire up the engine to look for a move.
        score = 0
        _depth = 0

        move, score = None, None
        if AI:
            if random_move:
                move = random_policy(hist[-1])
            else:
                start = time.time()
                for _depth, move, score in searcher.search(hist[-1], hist):
                    if time.time() - start > THINK_TIME:
                        break
        else:
            genmoves = set(hist[-1].gen_moves())
            while move not in genmoves:
                match = re.match('([a-i][0-9])' * 2, input('Your move: '))
                if match:
                    move = parse(match.group(1)), parse(match.group(2))
                    move = (254 - move[0], 254 - move[1])
                else:
                    # Inform the user when invalid input (e.g. "help") is entered
                    print("Please enter a move like h2e2")

        if score == MATE_UPPER:
            print("Checkmate!")

        # The black player moves from a rotated position, so we have to
        # 'back rotate' the move before printing it.
        if move is None:
            print("You win!")
            break

        # print("Think depth: {} My move: {} (score {})".format(_depth, render(254 - move[0]) + render(254 - move[1]), score))
        pos, win, eat, dst = hist[-1].mymove_check(move)

        if win:
            print("You lose, HAHAHAHAHAHAHAHAHAHA!")
            break

        rendered_eat = translate_eat(eat, dst, "BLACK", "CLEARMODE")
        if rendered_eat:
            AIeatlist.append(rendered_eat)

        hist.append(pos)


if __name__ == '__main__':
    main(random_move=False, AI=True)
