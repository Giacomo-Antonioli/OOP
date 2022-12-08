#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdlib.h>

#define MAX_VALUE 50

using namespace std;

typedef struct singleFileValues {
  int chip;
  int ch;
  float real_threshold;
  float x[MAX_VALUE] = {0};
  float y[MAX_VALUE] = {0};
} singleFileValues;

int read_single_file(singleFileValues *values, string filepath) {

  // singleFileValues values;
  string line;
  float test;
  int i = 0;

  stringstream ss(filepath);
  string token;
  for (int i = 0; i < 7; i++) {
    getline(ss, token, '/');
  }

  ss = std::stringstream(token); // token = "Ch_0_offset_0_Chip_001.txt"
  getline(ss, token, '_');
  getline(ss, token, '_');
  sscanf(token.c_str(), "%d", &values->ch);

  //#pragma unroll
  for (int i = 0; i < 4; i++) {
    getline(ss, token, '_'); // token = "001.txt"
  }

  ss = std::stringstream(token);
  getline(ss, token, '.');
  sscanf(token.c_str(), "%d", &values->chip);

  ifstream f(filepath);
  getline(f, line);
  ss = std::stringstream(line);
  getline(ss, token, '\t');

  if ((sscanf(token.c_str(), "%f", &test)) != 1) { // file errato
    values->real_threshold = -1;
    f.close();
    return -1;
  }

  getline(ss, token, '\t');
  sscanf(token.c_str(), "%f", &values->real_threshold);
  getline(f, line);
  getline(f, line);

  // cominciano i valori X e Y
  while (getline(f, line)) {
    ss = std::stringstream(line);
    getline(ss, token, '\t');
    sscanf(token.c_str(), "%f", &values->x[i]);
    getline(ss, token, '\t');
    sscanf(token.c_str(), "%f", &values->y[i]);
    i++;
  }

  f.close();
  return 0;
}

float polyfit(float X[MAX_VALUE], float Y[MAX_VALUE], float y_fit, int j) {
  // Dati i valori X e Y e dato il punto y, restituisce la x corrispondente.
  float acc_x = 0.0;
  float acc_y = 0.0;
  float media_x = 0.0;
  float media_y = 0.0;
  float cov = 0.0;
  float sqm = 0.0; // scarto quadr. medio di X
  float m = 0.0;
  float q = 0.0;

  for (int i = 0; i < j; i++) {
    acc_x += X[i];
    acc_y += Y[i];
  }
  media_x = acc_x / j;
  media_y = acc_y / j;
  for (int i = 0; i < j; i++) {
    cov += ((X[i] - media_x) * (Y[i] - media_y));
    sqm += ((X[i] - media_x) * (X[i] - media_x));
  }
  cov /= (j - 1);
  sqm /= (j - 1);
  sqm = sqrt(sqm);

  m = cov / (sqm * sqm);
  q = media_y - media_x * m;

  return (y_fit - q) / m;
}

int main(void) {

system("cd ../; ./analisi_file.sh");
system("cp ../file_path.txt ./file_path.txt");

 

  int tot_file = 6000;

  // cout << "Inserire numero file da analizzare: ";
  // cin >> tot_file;

  ifstream file_path("file_path.txt");
  ofstream risultati("risultati_cpp.txt");
  singleFileValues v;
  string onepath;

  int j = 0;
  float x_fit = 0.0;
  float X[MAX_VALUE] = {0};
  float Y[MAX_VALUE] = {0};

  auto start = chrono::steady_clock::now();

  for (int curr_file = 0; curr_file < tot_file; curr_file++) {

// Reset X e Y

    for (int i = 0; i < MAX_VALUE; i++) {
      X[i] = 0;
      Y[i] = 0;
    }

    getline(file_path, onepath);
    read_single_file(&v, onepath);

    if (v.real_threshold == -1) {
      continue;
    }

    j = 0;
    for (int i = 0; i < MAX_VALUE; i++) {
      if ((v.y[i] > 1) && (v.y[i] < 999)) {
        X[j] = v.x[i];
        Y[j] = v.y[i];
        j++;
      }
    }

    x_fit = polyfit(X, Y, 500, j);

    risultati << "Chip: " << v.chip << "\tCh: " << v.ch
              << "\tReal Thres: " << v.real_threshold
              << "\tThresh found: " << x_fit
              << "\tDiff: " << abs(x_fit - v.real_threshold) << "\n"
              << flush;
  }

  auto end = chrono::steady_clock::now();
  cout << "Tempo fit lineare C++: "
       << float(chrono::duration_cast<chrono::milliseconds>(end - start)
                    .count()) /
              1000
       << "s\n";

  file_path.close();
  risultati.close();
}