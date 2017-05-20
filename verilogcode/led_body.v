module led

  (
   input CLK,
   input RST,
   output reg [7:0] LED
   );
  parameter STEP = 10;
  parameter STEPa = 10;
  wire a;
  reg [31:0] count;
  
  always @(posedge CLK) begin
    if(RST) begin
      count <= 0;
      LED <= 0;
    end else begin
      if(count == STEP - 1) begin
        count <= 0;
        LED <= LED + STEP;
      end else begin
        count <= count + 1;
      end
    end
  end
endmodule
