program T41;
function F(x: integer): integer;
var y: integer;
begin
  y := x + 10;
  F := y;
end;
begin
  writeln(F(2));
end.
