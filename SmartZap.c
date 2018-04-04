#include <ncurses.h>

int main(int argc, char *argv[]) {
    initscr();

    WINDOW *win = newwin(10,10,1,1);

    //box(win, '*', '*');
    box(win, 0, 0); // 0 means use defaults
    touchwin(win);
    wrefresh(win);

    getchar();

    endwin();
    return 0;
}
