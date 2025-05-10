import java.util.Scanner;
public class Main {
    public static void main(String[]args){
        Scanner ob = new Scanner(System.in);
        System.out.println("enter a");
        int a = ob.nextInt();
        int sum = 0 ;
        do {
            sum= sum+(a%10);
            a= a/10;
        }while(a>0);
        System.out.println("sum:"+sum);
    }
}
