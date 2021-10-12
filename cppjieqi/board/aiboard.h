/*
* Created by Si Miao 2021/07/31
* Copyright (c) 2021. All rights reserved.
* Last modified 2021/07/31
*/
#ifndef aiboard_h
#define aiboard_h
#define MAX 257
#define CHESS_BOARD_SIZE 256
#define MAX_POSSIBLE_MOVES 120
#define A0 195 //(0, 0)坐标
#define I0 203 //(0, 8)坐标
#define A9 51 //(9, 0)坐标
#define I9 59 //(9, 8)坐标
#define NORTH -16
#define EAST 1
#define SOUTH 16
#define WEST -1

#include <cstddef>
#include <vector>
#include <string>
#include <tuple>
#include <set>
#include <unordered_map>
#include <iostream>
#include <functional>
#include <algorithm>
#include <cctype>
#include <cmath>
#include <random>
#include <chrono>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#include <ctype.h>
#include <stack>
#include <time.h>
#include <stdlib.h>
#include <tr1/functional>
#include "../log/log.h"
#include "../global/global.h"
#include "../score/score.h"
#include "thinker.h"
#define ROOTED 0
#define CLEAR_EVERY_DEPTH false

#define CLEAR_STACK(STACK) \
while(!STACK.empty()){ \
   STACK.pop(); \
} 
#define AISUM(VERSION) \
short numr = 0, numb = 0; \
numr += aidi[VERSION][1][INTR]; numr += aidi[VERSION][1][INTN];  numr += di[VERSION][1][INTB];  numr += aidi[VERSION][1][INTA];  numr += aidi[VERSION][1][INTC]; numr += aidi[VERSION][1][INTP]; \
numb += aidi[VERSION][0][INTr]; numb += aidi[VERSION][0][INTn];  numb += di[VERSION][0][INTb];  numb += aidi[VERSION][0][INTa];  numb += aidi[VERSION][0][INTc]; numb += aidi[VERSION][0][INTp]; \
aisumall[VERSION][1] = numr; aisumall[VERSION][0] = numb;

template <typename T, typename U, typename V>
bool GreaterTuple(const std::tuple<T, U, V> &i, const std::tuple<T, U, V> &j) {
        return std::get<0>(i) > std::get<0>(j);
}

extern short pst[123][256];
extern short average[VERSION_MAX][2][2][256];
extern unsigned char sumall[VERSION_MAX][2];
extern unsigned char di[VERSION_MAX][2][123];
extern std::unordered_map<std::string, std::pair<unsigned char, unsigned char>> kaijuku;
std::string mtd_thinker(void* self);
typedef short(*SCORE)(void* board_pointer, const char* state_pointer, unsigned char src, unsigned char dst);
typedef void(*KONGTOUPAO_SCORE)(void* board_pointer, short* kongtoupao_score, short* kongtoupao_score_opponent);
typedef std::string(*THINKER)(void* board_pointer);
inline void complicated_kongtoupao_score_function(void* board_pointer, short* kongtoupao_score, short* kongtoupao_score_opponent);
inline short complicated_score_function(void* self, const char* state_pointer, unsigned char src, unsigned char dst);
void register_score_functions();
std::string SearchScoreFunction(void* score_func, int type);
template <typename K, typename V>
extern V GetWithDefUnordered(const std::unordered_map<K,V>& m, const K& key, const V& defval);

template<typename T>
inline void hash_combine(std::size_t& seed, const T& val)
{
    std::hash<T> hasher;
    seed ^= hasher(val) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
}

//  taken from https://stackoverflow.com/a/7222201/916549
//
template<typename S, typename T>
struct myhash
{
    inline size_t operator()(const std::pair<S, T>& val) const
    {
        size_t seed = 0;
        hash_combine(seed, val.first);
        hash_combine(seed, val.second);
        return seed;
    }
};


namespace board{
class AIBoard : public Thinker{
public:
    short aiaverage[VERSION_MAX][2][2][256];
    unsigned char aisumall[VERSION_MAX][2];
    unsigned char aidi[VERSION_MAX][2][123];
    int version = 0;
    int round = 0;
    bool turn = true; //true红black黑
    unsigned char che = 0;
    unsigned char che_opponent = 0;
    unsigned char zu = 0;
    unsigned char covered = 0;
    unsigned char covered_opponent = 0;
    unsigned char endline = 0;
    short score_rough = 0;
    unsigned char kongtoupao = 0;
    unsigned char kongtoupao_opponent = 0;
    short kongtoupao_score = 0;
    short kongtoupao_score_opponent = 0;
    int rnci = 0;
    uint32_t zobrist_hash = 0;
    char state_red[MAX];
    char state_black[MAX];
    std::stack<std::tuple<unsigned char, unsigned char, char>> cache;
    short score;
    std::stack<short> score_cache;
    std::set<unsigned char> rooted_chesses;
    //tp_move: (zobrist_key, turn) --> move
    std::unordered_map<std::pair<uint32_t, bool>, std::pair<unsigned char, unsigned char>, myhash<uint32_t, bool>> tp_move;
    //tp_score: (zobrist_key, turn, depth <depth * 2 + turn>) --> (lower, upper)
    std::unordered_map<std::pair<uint32_t, int>, std::pair<short, short>, myhash<uint32_t, int>> tp_score;
    AIBoard() noexcept;
    AIBoard(const char another_state[MAX], bool turn, int round, const unsigned char di[5][2][123], short score) noexcept;
    AIBoard(const AIBoard& another_board) = delete;
    virtual ~AIBoard();
    void Reset() noexcept;
    void SetScoreFunction(std::string function_name, int type);
    std::string SearchScoreFunction(int type);
    std::vector<std::string> GetStateString() const;
    void Move(const unsigned char encode_from, const unsigned char encode_to, short score_step);
    void NULLMove();
    void UndoMove(int type);
    void Scan();
    void KongTouPao(const char* _state_pointer, int pos, bool t);
    void Rooted();
    template<bool needscore=true, bool return_after_mate=false> 
    bool GenMovesWithScore(std::tuple<short, unsigned char, unsigned char> legal_moves[MAX_POSSIBLE_MOVES], int& num_of_legal_moves, std::pair<unsigned char, unsigned char>* killer, short& killer_score, unsigned char& mate_src, unsigned char& mate_dst, bool& killer_is_alive);
    void OppoMateRooted(bool* mate_by_oppo,std::vector<unsigned char>* rooted);
    bool Ismate_After_Move(unsigned char src, unsigned char dst);
    void CopyData(const unsigned char di[5][2][123]);
    std::string Kaiju();
    virtual std::string Think();
    void PrintPos(bool turn) const;
    std::string DebugPrintPos(bool turn) const;
    void print_raw_board(const char* board, const char* hint);
    template<typename... Args> void print_raw_board(const char* board, const char* hint, Args... args);
    #if DEBUG
    std::vector<std::string> debug_flags;
    int movecounter=0;
    std::function<uint32_t()> get_theoretical_zobrist = [this]() -> uint32_t {
        uint32_t theoretical_hash = 0;
        for(int j = 51; j <= 203; ++j){
            if(::isalpha(state_red[j])){
                 theoretical_hash ^= _zobrist[(int)state_red[j]][j];
            }
        }
        return theoretical_hash;
    };
    std::function<std::string(std::pair<unsigned char, unsigned char>)> render = [this](std::pair<unsigned char, unsigned char> t) -> std::string {
        return translate_ucci(t.first, t.second);
    };
    #endif
    std::function<int(int)> translate_x = [](const int x) -> int {return 12 - x;};
    std::function<int(int)> translate_y = [](const int y) -> int {return 3 + y;};
    std::function<int(int, int)> translate_x_y = [](const int x, const int y) -> int{return 195 - 16 * x + y;};
    std::function<int(int, int)> encode = [](const int x, const int y) -> int {return 16 * x + y;};  
    std::function<int(int)> reverse = [](const int x) -> int {return 254 - x;};
    std::function<char(char)> swapcase = [](const char c) -> char{
       if(isalpha(c)) {
           return c ^ 32;
       }
       return c;
    };

    std::function<void(char*)> rotate = [this](char* p){
       std::reverse(p, p+255);
       std::transform(p, p+255, p, this -> swapcase);
       p[255] = ' ';
       memset(p + 256, 0, (MAX - 256) * sizeof(char));
    };
   
    std::function<const char*(void)> getstatepointer = [this](){
	   const char* _state_pointer = (this -> turn? this -> state_red : this -> state_black);
       return _state_pointer;
    };

    std::function<std::string(int)> translate_single = [](unsigned char i) -> std::string{
       int x1 = 12 - (i >> 4);
       int y1 = (i & 15) - 3;
       std::string ret = "  ";
       ret[0] = 'a' + y1;
       ret[1] = '0' + x1;
       return ret;
    };

    std::function<std::string(int, int)> translate_ucci = [this](unsigned char src, unsigned char dst) -> std::string{
       return translate_single(src) + translate_single(dst);
    };

    std::function<uint32_t(void)> randU32 = []() -> uint32_t{
       std::mt19937 gen(std::random_device{}());
       uint32_t randomNumber = gen();
       return randomNumber;
    };
   
private:
    uint32_t _zobrist[123][256];
    bool _has_initialized = false;
    static const int _chess_board_size;
    static const char _initial_state[MAX];
    static const std::unordered_map<std::string, std::string> _uni_pieces;
    static char _dir[91][8];
    SCORE _score_func = NULL;
    KONGTOUPAO_SCORE _kongtoupao_score_func = NULL;
    THINKER _thinker_func = NULL;
    std::function<std::string(const char)> _getstring = [](const char c) -> std::string {
        std::string ret;
        const std::string c_string(1, c);
        ret = GetWithDefUnordered<std::string, std::string>(_uni_pieces, c_string, c_string);
        return ret;
    };
    std::function<std::string(int, int, bool)> _getstringxy = [this](int x, int y, bool turn) -> std::string {
        std::string ret =  turn?_getstring(state_red[encode(x, y)]):_getstring(state_black[encode(x, y)]);
        return ret;
    };
    std::function<void(void)> _initialize_zobrist = [this](){
        for(int i = 0; i < 123; ++i){
            for(int j = 0; j < 256; ++j){
                if(i != '.')
                    _zobrist[i][j] = randU32();
                else
                    _zobrist[i][j] = 0;
            }
        }
        for(int j = 51; j <= 203; ++j){
            if(::isalpha(state_red[j])){
                zobrist_hash ^= _zobrist[(int)state_red[j]][j];
            }
        }
    };
    void _initialize_dir();
};
}

short mtd_quiescence(board::AIBoard* self, const short gamma, int quiesc_depth, const bool root);
short mtd_alphabeta(board::AIBoard* self, const short gamma, int depth, const bool root, const bool nullmove, const bool nullmove_now, const int quiesc_depth);

#endif
