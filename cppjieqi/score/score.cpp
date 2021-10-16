#include "score.h"
short pstglobal[2][123][256];

bool read_score_table(const char* score_file, short pst[123][256]){
    std::unordered_map<char, bool> is_read;
    is_read['R'] = is_read['N'] = is_read['B'] = is_read['A'] = is_read['K'] = is_read['C'] = is_read['P'] = false;

    memset(pst, 0, 123 * 256);
    std::ifstream instream(score_file);
    std::string line = "";
    constexpr int M = 10;
    constexpr int N = 9;
    int state_machine = M;
    char key = '\0';

    if(!instream.is_open()) {
        printf("[FAILED 0]score --> score.cpp --> read_score_table --> Open %s FAILED!\n", score_file);
        RETURN;
    }

    while(std::getline(instream, line)){
        std::string tmpline = subtrim(line);
        int len = tmpline.size();
        if(len == 0){
            continue;
        }else if(len == 1 && isupper(tmpline[0])){
            if(state_machine == M){
                state_machine = 0;
                key = tmpline[0];
                if(MINGZI.find(key) == std::string::npos){
                    printf("[FAILED 1]score --> score.cpp --> read_score_table --> Read key FAILED! state_machine = %d, key = %c\n", state_machine, key);
                    RETURN;
                }
                is_read[key] = true;
                continue;
            } else{
                printf("[FAILED 2]score --> score.cpp --> read_score_table --> Read key FAILED! state_machine = %d\n", state_machine);
                RETURN;
            }
        }else{
            if(state_machine < 0 || state_machine >= M){
                printf("[FAILED 3]score --> score.cpp --> read_score_table --> Read key FAILED (counter != N)! state_machine = %d\n", state_machine);
                RETURN;
            }
            std::stringstream ss;
            ss << tmpline;
            int counter = 0;
            int tmpint = 0;
            while(ss >> tmpint){
                pst[(int)key][ENCODE(state_machine, counter)] = tmpint;
                ++counter;
                if(counter > N){
                    break;
                } //counter > N
            } // ss >> tmpint
            if(counter != N) {
                printf("[FAILED 4]score --> score.cpp --> read_score_table --> Read key FAILED (counter != N)! state_machine = %d, counter = %d, N = %d\n", state_machine, counter, N);
                RETURN;
            }
            ++state_machine;
        }
    }
    bool ret = true;
    for(auto it = is_read.begin(); it != is_read.end(); ++it){
        if(!it -> second){
            ret = false;
            printf("%c not initialized!\n", it -> first);
        }
    }
    if(!ret) { RETURN; }
    return true;
}

void copy_pst(short dst[][256], short src[][256]){
    for(char c:MINGZI){
        memcpy(dst[(int)c], src[(int)c], 256*sizeof(short));
    }
}

bool read_kaijuku(const char* kaijuku_file, std::unordered_map<std::string, std::pair<unsigned char, unsigned char>>& kaijuku){
    std::ifstream instream(kaijuku_file);
    if(!instream.is_open()) {
        printf("[FAILED 0]score --> score.cpp --> read_kaijuku --> Open %s FAILED!\n", kaijuku_file);
        return false;
    }
    std::string line = "";
    std::string key = "";
    int state = 0, counter = 0;
    while(std::getline(instream, line)){
        std::string tmpline = subtrim(line);
        int len = tmpline.size();
        if(len == 0){
            continue;
        }
        if(!state){
            if(tmpline.size() != 256){
                printf("[FAILED 1]score --> score.cpp --> read_kaijuku --> size error! line.size() = %zu\n", tmpline.size());
                return false;
            }
            key += std::regex_replace(tmpline, std::regex("@"), " ");
        }else{
            unsigned char a = 0, b = 0;
            int num = 0;
            for(size_t i = 0; i < tmpline.size(); ++i){
                if(!::isdigit(tmpline[i]) && tmpline[i] != ' ') {printf("[FAILED 2]score --> score.cpp --> read_kaijuku --> format error\n"); return false;}
                if(::isdigit(tmpline[i])){
                    if(num == 0){
                        a = a * 10 + tmpline[i] - '0';
                    }
                    if(num == 1){
                        b = b * 10 + tmpline[i] - '0';
                    }
                }
                else if(tmpline[i] == ' '){
                    if(num == 0) {num = 1;}
                    if(num == 1) {continue;}
                    if(num == 2) {printf("[FAILED 2]score --> score.cpp --> read_kaijuku --> format error\n"); return false;}
                }
            }
            kaijuku[std::string(key)] = {a, b};
            key = "";
            ++counter;
        }
        state = (state + 1) % 2;
    }
    return true;
}
