#include <iostream>
#include <fstream>
#include <ostream>


int main() {
    int i = 1;
    double a[100];
    std::ifstream infile("/Users/yanggongchi/Desktop/random_data.txt");
    std::ofstream outfile("/Users/yanggongchi/Desktop/outfile.txt");
    if (!infile) {
    std::cout << "can't open input.dat file to read\n";
    exit(1);
    }
    if (!outfile) {
    std::cout << "can't open output.dat file to write\n";
    exit(2);
    }

    while(!infile.eof()){
        infile>>a[i];
        std::cout<<a[i]<<std::endl;
        outfile << a[i] << " ";
        std::cout << a[i] << " ";
        ++i;
    }
    infile.close();
    outfile.close();
    return 0;
}

/*int main()
{
    int i = 0;
    std::ifstream infile;
    infile.open("random_data.txt");
    double a[100];
    while(!infile.eof()){
        infile>>a[i++];
    }
    std::cout<<a<<std::endl;
    infile.close();
    /*std::ofstream outfile("./output.txt");
    double a[100];
    int i=0;
    while(!infile.eof()){
        infile>>a[i];
        outfile << a[i] << " ";
        std::cout << a[i] << " ";
        ++i;
    }
    infile.close();
    outfile.close();
    */


